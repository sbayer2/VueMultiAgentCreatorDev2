import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient } from '@/utils/api'
import type { ChatSession, Message, MessageFile, SendMessageData, StreamMessage } from '@/types'
import { useWebSocket } from '@/composables/useWebSocket'

export const useChatStore = defineStore('chat', () => {
  // State
  const sessions = ref<ChatSession[]>([])
  const currentSession = ref<ChatSession | null>(null)
  const isLoading = ref(false)
  const isSending = ref(false)
  const error = ref<string | null>(null)
  const streamingMessage = ref<string>('')
  
  // WebSocket instance
  let ws: ReturnType<typeof useWebSocket> | null = null

  // Getters
  const sessionsList = computed(() => sessions.value)
  const currentMessages = computed(() => currentSession.value?.messages || [])
  const hasActiveSession = computed(() => !!currentSession.value)
  const isStreaming = computed(() => !!streamingMessage.value)

  // Actions
  const fetchSessions = async () => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiClient.get<ChatSession[]>('/chat/sessions')
      
      if (response.success && response.data) {
        sessions.value = response.data
        return { success: true, data: response.data }
      } else {
        error.value = response.error?.message || 'Failed to fetch sessions'
        return { success: false, error: error.value }
      }
    } catch (err) {
      error.value = 'An unexpected error occurred'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  const createSession = async (assistantId: string, title?: string) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiClient.post<ChatSession>('/chat/sessions', {
        assistantId,
        title: title || 'New Chat',
      })
      
      if (response.success && response.data) {
        sessions.value.unshift(response.data)
        currentSession.value = response.data
        return { success: true, data: response.data }
      } else {
        error.value = response.error?.message || 'Failed to create session'
        return { success: false, error: error.value }
      }
    } catch (err) {
      error.value = 'An unexpected error occurred'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  const loadSession = async (sessionId: string) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiClient.get<ChatSession>(`/chat/sessions/${sessionId}`)
      
      if (response.success && response.data) {
        currentSession.value = response.data
        
        // Update in list if exists
        const index = sessions.value.findIndex(s => s.id === sessionId)
        if (index !== -1) {
          sessions.value[index] = response.data
        }
        
        return { success: true, data: response.data }
      } else {
        error.value = response.error?.message || 'Failed to load session'
        return { success: false, error: error.value }
      }
    } catch (err) {
      error.value = 'An unexpected error occurred'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  const sendMessage = async (content: string, files?: File[]) => {
    if (!currentSession.value) {
      error.value = 'No active session'
      return { success: false, error: error.value }
    }

    isSending.value = true
    error.value = null
    streamingMessage.value = ''

    // Process files if provided
    let messageFiles: MessageFile[] | undefined
    if (files && files.length > 0) {
      messageFiles = files.map(file => ({
        id: `file-${Date.now()}-${Math.random()}`,
        name: file.name,
        size: file.size,
        type: file.type,
      }))
    }

    // Add user message to current session
    const userMessage: Message = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
      metadata: messageFiles ? { files: messageFiles } : undefined,
    }
    currentSession.value.messages.push(userMessage)

    try {
      // Check if WebSocket streaming is supported
      const streamSupported = 'WebSocket' in window && ws?.isConnected.value

      if (streamSupported) {
        // Use WebSocket for streaming
        return new Promise((resolve) => {
          let assistantMessage: Message | null = null

          // Set up message handlers
          const handleStreamMessage = (data: StreamMessage) => {
            if (data.type === 'start') {
              assistantMessage = {
                id: data.messageId,
                role: 'assistant',
                content: '',
                timestamp: new Date().toISOString(),
              }
              currentSession.value!.messages.push(assistantMessage)
            } else if (data.type === 'token' && assistantMessage) {
              assistantMessage.content += data.content
              streamingMessage.value = assistantMessage.content
            } else if (data.type === 'end') {
              streamingMessage.value = ''
              // Remove event listeners
              ws?.off('stream-message', handleStreamMessage)
              ws?.off('stream-error', handleStreamError)
              resolve({ success: true })
            }
          }

          const handleStreamError = (data: StreamMessage) => {
            if (data.type === 'error') {
              streamingMessage.value = ''
              error.value = data.error
              // Remove event listeners
              ws?.off('stream-message', handleStreamMessage)
              ws?.off('stream-error', handleStreamError)
              resolve({ success: false, error: error.value })
            }
          }

          // Register event handlers
          ws?.on('stream-message', handleStreamMessage)
          ws?.on('stream-error', handleStreamError)

          // Send message via WebSocket
          ws?.send({
            type: 'send-message',
            sessionId: currentSession.value.id,
            content,
            files: messageFiles,
          })
        })
      } else {
        // Fallback to regular API call
        const formData = new FormData()
        formData.append('content', content)
        
        // Add files if present
        if (files) {
          files.forEach((file, index) => {
            formData.append(`files[${index}]`, file)
          })
        }
        
        const response = await apiClient.post<Message>(
          `/chat/sessions/${currentSession.value.id}/messages`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          }
        )
        
        if (response.success && response.data) {
          currentSession.value.messages.push(response.data)
          return { success: true, data: response.data }
        } else {
          // Remove user message on error
          currentSession.value.messages.pop()
          error.value = response.error?.message || 'Failed to send message'
          return { success: false, error: error.value }
        }
      }
    } catch (err) {
      // Remove user message on error
      currentSession.value.messages.pop()
      error.value = 'An unexpected error occurred'
      return { success: false, error: error.value }
    } finally {
      isSending.value = false
    }
  }

  const deleteSession = async (sessionId: string) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiClient.delete(`/chat/sessions/${sessionId}`)
      
      if (response.success) {
        sessions.value = sessions.value.filter(s => s.id !== sessionId)
        
        if (currentSession.value?.id === sessionId) {
          currentSession.value = null
        }
        
        return { success: true }
      } else {
        error.value = response.error?.message || 'Failed to delete session'
        return { success: false, error: error.value }
      }
    } catch (err) {
      error.value = 'An unexpected error occurred'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  const clearCurrentSession = () => {
    currentSession.value = null
    streamingMessage.value = ''
  }

  const updateSessionTitle = async (sessionId: string, title: string) => {
    try {
      const response = await apiClient.patch<ChatSession>(
        `/chat/sessions/${sessionId}`,
        { title }
      )
      
      if (response.success && response.data) {
        // Update in list
        const index = sessions.value.findIndex(s => s.id === sessionId)
        if (index !== -1) {
          sessions.value[index] = response.data
        }
        
        // Update current if it's the same
        if (currentSession.value?.id === sessionId) {
          currentSession.value = response.data
        }
        
        return { success: true, data: response.data }
      } else {
        return { success: false, error: response.error?.message }
      }
    } catch (err) {
      return { success: false, error: 'Failed to update title' }
    }
  }

  // Initialize WebSocket connection
  const initializeWebSocket = () => {
    if (!ws) {
      const wsUrl = import.meta.env.VITE_WS_URL || `ws://${window.location.host}/ws`
      ws = useWebSocket({
        url: wsUrl,
        reconnect: true,
        reconnectDelay: 3000,
        reconnectAttempts: 5,
      })
    }
  }

  // Disconnect WebSocket
  const disconnectWebSocket = () => {
    if (ws) {
      ws.disconnect()
      ws = null
    }
  }

  return {
    // State
    sessions,
    currentSession,
    isLoading,
    isSending,
    error,
    streamingMessage,
    
    // Getters
    sessionsList,
    currentMessages,
    hasActiveSession,
    isStreaming,
    
    // Actions
    fetchSessions,
    createSession,
    loadSession,
    sendMessage,
    deleteSession,
    clearCurrentSession,
    updateSessionTitle,
    initializeWebSocket,
    disconnectWebSocket,
  }
})