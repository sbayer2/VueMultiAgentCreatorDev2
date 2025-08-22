import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient } from '@/utils/api'
import { useAssistantsStore } from '@/stores/assistants'
import type { 
  Conversation, 
  ConversationMessage, 
  CreateConversationData, 
  SendMessageData,
  ChatResponse,
  StreamMessage,
  ImageAttachment
} from '@/types'
import { useWebSocket } from '@/composables/useWebSocket'
import { useAssistantsStore } from './assistants'

export const useConversationsStore = defineStore('conversations', () => {
  // State
  const conversations = ref<Conversation[]>([])
  const currentConversation = ref<Conversation | null>(null)
  const currentMessages = ref<ConversationMessage[]>([])
  const isLoading = ref(false)
  const isSending = ref(false)
  const error = ref<string | null>(null)
  const streamingContent = ref<string>('')
  
  // WebSocket instance
  let ws: ReturnType<typeof useWebSocket> | null = null
  const wsConnections = new Map<number, ReturnType<typeof useWebSocket>>()

  // Getters
  const conversationsList = computed(() => conversations.value)
  const conversationsCount = computed(() => conversations.value.length)
  const hasActiveConversation = computed(() => !!currentConversation.value)
  const isStreaming = computed(() => !!streamingContent.value)
  const getConversationById = computed(() => (id: number) => 
    conversations.value.find(c => c.id === id)
  )

  // Actions  
  const fetchConversations = async (assistantId?: number) => {
    // For thread-based API, we'll maintain a simple local list
    // Threads are created as-needed and managed by the backend
    isLoading.value = true
    error.value = null

    try {
      // For now, return empty - threads are created on-demand
      conversations.value = []
      return { success: true, data: [] }
    } catch (err) {
      error.value = 'An unexpected error occurred'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  const createConversation = async (data: CreateConversationData) => {
    isLoading.value = true
    error.value = null

    try {
      // For thread-based approach, we don't create separate conversations
      // Instead, set the current assistant and let the user start chatting
      // The backend will handle thread creation/reuse automatically
      
      // Create a simple conversation object to track the current assistant
      const newConversation: Conversation = {
        id: data.assistant_id, // Use assistant ID as conversation ID for thread-based approach
        assistant_id: data.assistant_id,
        title: data.title || 'New Chat',
        message_count: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        thread_id: '' // Will be handled by backend
      }
      
      // Don't add to conversations list - use it as temporary current conversation
      currentConversation.value = newConversation
      currentMessages.value = []
      return { success: true, data: newConversation }
    } catch (err) {
      error.value = 'An unexpected error occurred'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  const loadConversation = async (conversationId: number) => {
    isLoading.value = true
    error.value = null

    try {
      // For thread-based approach, conversationId is actually the assistant ID
      // Get the assistant from the assistants store
      const assistantsStore = useAssistantsStore()
      const assistant = assistantsStore.getAssistantById(conversationId)
      
      if (assistant) {
        // Create a conversation context for this assistant
        const conversation: Conversation = {
          id: assistant.id, // Use assistant ID as conversation ID
          assistant_id: assistant.id,
          title: `Chat with ${assistant.name}`,
          message_count: 0,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          thread_id: '' // Will be handled by backend
        }
        
        currentConversation.value = conversation
        currentMessages.value = []
        
        return { success: true, data: conversation }
      } else {
        error.value = 'Assistant not found'
        return { success: false, error: error.value }
      }
    } catch (err) {
      error.value = 'An unexpected error occurred'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  // WebSocket streaming function
  const sendMessageViaWebSocket = async (content: string, previousResponseId?: string, attachments?: ImageAttachment[]): Promise<{ success: boolean; data?: ChatResponse; error?: string }> => {
    if (!currentConversation.value) {
      return { success: false, error: 'No active conversation' }
    }

    const conversationId = currentConversation.value.id
    let wsConnection = wsConnections.get(conversationId)

    // Create WebSocket connection if it doesn't exist or is not connected
    if (!wsConnection || !wsConnection.isConnected.value) {
      wsConnection = await connectToConversationWebSocket(conversationId)
      if (!wsConnection) {
        return { success: false, error: 'Failed to establish WebSocket connection' }
      }
    }

    return new Promise<{ success: boolean; data?: ChatResponse; error?: string }>((resolve) => {
      let assistantMessage: ConversationMessage | null = null
      let isResolved = false

      const cleanup = () => {
        if (wsConnection) {
          wsConnection.off('connection')
          wsConnection.off('text_delta')
          wsConnection.off('image_output')  // MMACTEMP image support
          wsConnection.off('complete')
          wsConnection.off('error')
          wsConnection.off('tool_call_start')
          wsConnection.off('tool_call_delta')
          wsConnection.off('tool_call_complete')
        }
      }

      const handleConnection = (data: any) => {
        if (data.type === 'connection' && currentConversation.value) {
          currentConversation.value.message_count = data.message_count || 0
          if (data.thread_id) {
            currentConversation.value.thread_id = data.thread_id
          }
        }
      }

      const handleTextDelta = (data: any) => {
        if (data.type === 'text_delta') {
          if (!assistantMessage) {
            assistantMessage = {
              id: Date.now() + 1,
              role: 'assistant',
              content: '',
              created_at: new Date().toISOString(),
            }
            currentMessages.value.push(assistantMessage)
          }
          assistantMessage.content += data.content
          streamingContent.value = assistantMessage.content
        }
      }

      const handleImageOutput = (data: any) => {
        if (data.type === 'image_output' && assistantMessage) {
          // Add image attachments to the message (MMACTEMP pattern)
          const imageAttachments = data.images.map((img: any) => ({
            id: img.file_id,
            file_id: img.file_id,
            name: `Generated Image`,
            type: 'image_file',
            url: `/api/files/${img.file_id}/content`,
            preview_url: `/api/files/${img.file_id}/content`
          }))
          
          assistantMessage.attachments = (assistantMessage.attachments || []).concat(imageAttachments)
        }
      }

      const handleComplete = (data: any) => {
        if (data.type === 'complete') {
          streamingContent.value = ''
          if (assistantMessage) {
            assistantMessage.content = data.content
          }
          
          if (!isResolved) {
            isResolved = true
            cleanup()
            resolve({
              success: true,
              data: {
                message_id: assistantMessage?.id || 0,
                conversation_id: conversationId,
                content: data.content,
                response_id: data.response_id
              }
            })
          }
        }
      }

      const handleError = (data: any) => {
        if (data.type === 'error') {
          streamingContent.value = ''
          error.value = data.message
          // Remove the user message on error
          if (currentMessages.value.length > 0 && currentMessages.value[currentMessages.value.length - 1].role === 'user') {
            currentMessages.value.pop()
          }
          
          if (!isResolved) {
            isResolved = true
            cleanup()
            resolve({ success: false, error: data.message })
          }
        }
      }

      const handleToolCallStart = (data: any) => {
        if (data.type === 'tool_call_start' && assistantMessage) {
          assistantMessage.content += `\n[Using ${data.tool_name}...]`
        }
      }

      const handleToolCallDelta = (data: any) => {
        if (data.type === 'tool_call_delta' && assistantMessage && data.content) {
          assistantMessage.content += data.content
        }
      }

      const handleToolCallComplete = (data: any) => {
        if (data.type === 'tool_call_complete' && assistantMessage) {
          assistantMessage.content += `\n[${data.tool_name} completed]`
        }
      }

      // Register event handlers
      wsConnection!.on('connection', handleConnection)
      wsConnection!.on('text_delta', handleTextDelta)
      wsConnection!.on('image_output', handleImageOutput)  // MMACTEMP image support
      wsConnection!.on('complete', handleComplete)
      wsConnection!.on('error', handleError)
      wsConnection!.on('tool_call_start', handleToolCallStart)
      wsConnection!.on('tool_call_delta', handleToolCallDelta)
      wsConnection!.on('tool_call_complete', handleToolCallComplete)

      // Send message via WebSocket - match backend's expected format
      const messageData: any = {
        type: 'message',
        content,
        assistant_id: currentConversation.value.assistant_id,
      }
      
      // Add file_ids if attachments exist (backend expects file_ids array)
      if (attachments && attachments.length > 0) {
        messageData.file_ids = attachments.map(att => att.file_id)
      }
      
      const success = wsConnection!.send(messageData)

      if (!success) {
        cleanup()
        resolve({ success: false, error: 'Failed to send message via WebSocket' })
      }

      // Timeout after 30 seconds
      setTimeout(() => {
        if (!isResolved) {
          isResolved = true
          cleanup()
          resolve({ success: false, error: 'Message timeout' })
        }
      }, 30000)
    })
  }

  // Function to connect to thread WebSocket (using backend's pattern)
  const connectToConversationWebSocket = async (conversationId: number): Promise<ReturnType<typeof useWebSocket> | null> => {
    try {
      // Get auth token
      const token = localStorage.getItem('auth_token')
      if (!token) {
        error.value = 'No authentication token found'
        return null
      }

      // Build WebSocket URL using backend's thread-based pattern
      const apiUrl = import.meta.env.VITE_API_URL || `${window.location.origin}/api`
      const wsProtocol = apiUrl.startsWith('https://') ? 'wss://' : 'ws://'
      // Remove /api from the end if present to get base backend URL
      const backendBaseUrl = apiUrl.replace(/\/api$/, '')
      const wsHost = backendBaseUrl.replace(/^https?:\/\//, '')
      const wsUrl = `${wsProtocol}${wsHost}/api/chat/ws/${encodeURIComponent(token)}`

      const wsConnection = useWebSocket({
        url: wsUrl,
        reconnect: true,
        reconnectDelay: 3000,
        reconnectAttempts: 3,
        heartbeat: true,
        heartbeatInterval: 30000,
        heartbeatMessage: 'ping'
      })

      // Wait for connection
      return new Promise((resolve) => {
        const timeout = setTimeout(() => {
          resolve(null)
        }, 10000)

        wsConnection.on('connected', () => {
          clearTimeout(timeout)
          wsConnections.set(conversationId, wsConnection)
          resolve(wsConnection)
        })

        wsConnection.on('error', () => {
          clearTimeout(timeout)
          resolve(null)
        })
      })
    } catch (err) {
      error.value = 'Failed to connect to WebSocket'
      return null
    }
  }

  const sendMessage = async (content: string, assistantId?: number, previousResponseId?: string, attachments?: ImageAttachment[]) => {
    if (!currentConversation.value && !assistantId) {
      error.value = 'No active conversation and no assistant specified'
      return { success: false, error: error.value }
    }

    isSending.value = true
    error.value = null
    streamingContent.value = ''

    // Add user message to current messages with attachments
    const userMessage: ConversationMessage = {
      id: Date.now(), // Temporary ID
      role: 'user',
      content,
      created_at: new Date().toISOString(),
      attachments: attachments && attachments.length > 0 ? attachments : undefined,
    }
    currentMessages.value.push(userMessage)

    try {
      const messageData: SendMessageData = {
        content,
        assistant_id: assistantId || currentConversation.value!.assistant_id,
        conversation_id: currentConversation.value?.id,
        attachments: attachments && attachments.length > 0 ? attachments : undefined,
      }

      // Add previous_response_id if provided for conversation continuity
      const requestData = previousResponseId 
        ? { ...messageData, previous_response_id: previousResponseId }
        : messageData

      // Get the actual OpenAI assistant ID (not database ID)
      const assistantsStore = useAssistantsStore()
      let openaiAssistantId: string
      
      // Get the database assistant ID to look up
      const dbAssistantId = assistantId || currentConversation.value!.assistant_id
      
      // Look up the OpenAI assistant ID from the database ID
      const assistant = assistantsStore.getAssistantById(dbAssistantId)
      if (!assistant) {
        error.value = 'Assistant not found'
        return { success: false, error: error.value }
      }
      openaiAssistantId = assistant.assistant_id

      // Use HTTP chat endpoint (WebSocket fallback for Cloud Run)
      const chatData = {
        content,
        assistant_id: openaiAssistantId,
        file_ids: attachments ? attachments.map(att => att.file_id) : []
      }
      
      const response = await apiClient.post<{ 
        message_id: string; 
        content: string; 
        attachments?: Array<{file_id: string; type: string}> 
      }>('/chat/message', chatData)
      
      // Debug: response working correctly!
      
      if (response.success && response.data) {
        // Process image attachments from backend response
        let imageAttachments: ImageAttachment[] = []
        if (response.data.attachments) {
          imageAttachments = response.data.attachments.map((att: any) => ({
            id: att.file_id,
            file_id: att.file_id,
            name: `image_${att.file_id.slice(-8)}.png`,
            size: 0,
            type: att.type,
            url: `${import.meta.env.VITE_API_URL}/files/openai/${att.file_id}`,
            preview_url: `${import.meta.env.VITE_API_URL}/files/openai/${att.file_id}`
          }))
        }
        
        const assistantMessage: ConversationMessage = {
          id: parseInt(response.data.message_id) || Date.now(),
          role: 'assistant',
          content: response.data.content,
          created_at: new Date().toISOString(),
          attachments: imageAttachments.length > 0 ? imageAttachments : undefined
        }
        
        currentMessages.value.push(assistantMessage)
        
        // Update conversation message count
        if (currentConversation.value) {
          currentConversation.value.message_count += 2 // user + assistant message
          currentConversation.value.updated_at = new Date().toISOString()
        }
        
        return { success: true, data: response.data }
      } else {
        // Remove user message on error
        currentMessages.value.pop()
        error.value = response.error?.message || 'Failed to send message'
        return { success: false, error: error.value }
      }
    } catch (err) {
      // Remove user message on error
      currentMessages.value.pop()
      error.value = 'An unexpected error occurred'
      return { success: false, error: error.value }
    } finally {
      isSending.value = false
    }
  }

  const deleteConversation = async (conversationId: number) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiClient.delete(`/chat/conversations/${conversationId}`)
      
      if (response.success) {
        conversations.value = conversations.value.filter(c => c.id !== conversationId)
        
        if (currentConversation.value?.id === conversationId) {
          currentConversation.value = null
          currentMessages.value = []
        }
        
        return { success: true }
      } else {
        error.value = response.error?.message || 'Failed to delete conversation'
        return { success: false, error: error.value }
      }
    } catch (err) {
      error.value = 'An unexpected error occurred'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  const updateConversationTitle = async (conversationId: number, title: string) => {
    try {
      const response = await apiClient.put<Conversation>(
        `/chat/conversations/${conversationId}`,
        { title }
      )
      
      if (response.success && response.data) {
        // Update in list
        const index = conversations.value.findIndex(c => c.id === conversationId)
        if (index !== -1) {
          conversations.value[index] = response.data
        }
        
        // Update current if it's the same
        if (currentConversation.value?.id === conversationId) {
          currentConversation.value = response.data
        }
        
        return { success: true, data: response.data }
      } else {
        return { success: false, error: response.error?.message }
      }
    } catch (err) {
      return { success: false, error: 'Failed to update title' }
    }
  }

  const clearCurrentConversation = () => {
    currentConversation.value = null
    currentMessages.value = []
    streamingContent.value = ''
  }

  const clearError = () => {
    error.value = null
  }

  const resetState = () => {
    conversations.value = []
    currentConversation.value = null
    currentMessages.value = []
    isLoading.value = false
    isSending.value = false
    error.value = null
    streamingContent.value = ''
  }

  // WebSocket management
  const initializeWebSocket = () => {
    // WebSocket connections are now created per conversation as needed
    // This function is kept for compatibility but doesn't do anything
  }

  const disconnectWebSocket = () => {
    // Disconnect all conversation WebSocket connections
    for (const [conversationId, wsConnection] of wsConnections) {
      wsConnection.disconnect()
    }
    wsConnections.clear()
    
    if (ws) {
      ws.disconnect()
      ws = null
    }
  }

  const disconnectConversationWebSocket = (conversationId: number) => {
    const wsConnection = wsConnections.get(conversationId)
    if (wsConnection) {
      wsConnection.disconnect()
      wsConnections.delete(conversationId)
    }
  }

  return {
    // State
    conversations,
    currentConversation,
    currentMessages,
    isLoading,
    isSending,
    error,
    streamingContent,
    
    // Getters
    conversationsList,
    conversationsCount,
    hasActiveConversation,
    isStreaming,
    getConversationById,
    
    // Actions
    fetchConversations,
    createConversation,
    loadConversation,
    sendMessage,
    deleteConversation,
    updateConversationTitle,
    clearCurrentConversation,
    clearError,
    resetState,
    initializeWebSocket,
    disconnectWebSocket,
    disconnectConversationWebSocket,
  }
})