<template>
  <div class="chat-view h-screen flex bg-gray-50">
    <!-- Assistants Sidebar -->
    <aside class="w-80 bg-white border-r border-gray-200 flex flex-col">
      <div class="p-4 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900">Assistants</h2>
      </div>
      <AssistantSelector 
        :assistants="assistantsList"
        :selected-assistant-id="selectedAssistantId"
        :is-loading="assistantsLoading"
        @select="handleAssistantSelect"
      />
    </aside>

    <!-- Main Chat Area -->
    <main class="flex-1 flex flex-col">
      <!-- Chat Header -->
      <header class="bg-white border-b border-gray-200 px-6 py-4">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-xl font-semibold text-gray-900">
              {{ currentSession?.title || 'New Chat' }}
            </h1>
            <p v-if="selectedAssistant" class="text-sm text-gray-500 mt-1">
              Chatting with {{ selectedAssistant.name }}
            </p>
          </div>
          <div class="flex items-center space-x-3">
            <button
              v-if="currentSession"
              @click="handleNewChat"
              class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              New Chat
            </button>
          </div>
        </div>
      </header>

      <!-- Messages Area -->
      <div class="flex-1 overflow-y-auto px-6 py-4" ref="messagesContainer">
        <div v-if="!currentSession && !selectedAssistant" class="flex items-center justify-center h-full">
          <div class="text-center">
            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900">No assistant selected</h3>
            <p class="mt-1 text-sm text-gray-500">Select an assistant from the sidebar to start chatting</p>
          </div>
        </div>

        <div v-else-if="!currentSession" class="flex items-center justify-center h-full">
          <div class="text-center">
            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900">Start a new conversation</h3>
            <p class="mt-1 text-sm text-gray-500">Send a message to {{ selectedAssistant.name }} to begin</p>
          </div>
        </div>

        <div v-else class="space-y-4">
          <ChatMessage
            v-for="message in currentMessages"
            :key="message.id"
            :message="message"
            :is-streaming="isStreaming && message.id === streamingMessageId"
            :streaming-content="streamingMessage"
          />
        </div>
      </div>

      <!-- Input Area -->
      <div class="bg-white border-t border-gray-200 px-6 py-4">
        <form @submit.prevent="handleSendMessage" class="flex items-end space-x-3">
          <div class="flex-1">
            <label for="message-input" class="sr-only">Message</label>
            <div class="relative">
              <textarea
                id="message-input"
                v-model="messageInput"
                @keydown.enter.prevent="handleKeyDown"
                :disabled="!selectedAssistant || isSending"
                rows="3"
                class="block w-full resize-none rounded-md border-gray-300 pr-10 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                :placeholder="selectedAssistant ? `Message ${selectedAssistant.name}...` : 'Select an assistant to start chatting'"
              />
              <div class="absolute bottom-2 right-2">
                <label for="file-upload" class="cursor-pointer">
                  <input
                    id="file-upload"
                    type="file"
                    multiple
                    @change="handleFileUpload"
                    :disabled="!selectedAssistant || isSending"
                    class="sr-only"
                  />
                  <svg class="h-5 w-5 text-gray-400 hover:text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                  </svg>
                </label>
              </div>
            </div>
            <div v-if="attachedFiles.length > 0" class="mt-2 flex flex-wrap gap-2">
              <div
                v-for="(file, index) in attachedFiles"
                :key="index"
                class="flex items-center space-x-1 bg-gray-100 px-2 py-1 rounded-md text-sm"
              >
                <svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <span class="text-gray-700">{{ file.name }}</span>
                <span class="text-gray-400 text-xs">({{ formatFileSize(file.size) }})</span>
                <button
                  type="button"
                  @click="removeFile(index)"
                  class="text-gray-400 hover:text-gray-500"
                >
                  <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
          <button
            type="submit"
            :disabled="!selectedAssistant || !messageInput.trim() || isSending"
            class="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg v-if="isSending" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>{{ isSending ? 'Sending...' : 'Send' }}</span>
          </button>
        </form>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useAssistantsStore } from '@/stores/assistants'
import { useChatStore } from '@/stores/chat'
import AssistantSelector from '@/components/chat/AssistantSelector.vue'
import ChatMessage from '@/components/chat/ChatMessage.vue'
import type { Assistant } from '@/types'

const route = useRoute()
const router = useRouter()
const assistantsStore = useAssistantsStore()
const chatStore = useChatStore()

// Store refs
const { assistants: assistantsList, isLoading: assistantsLoading } = storeToRefs(assistantsStore)
const { 
  currentSession, 
  currentMessages, 
  isSending, 
  isStreaming,
  streamingMessage 
} = storeToRefs(chatStore)

// Local state
const messageInput = ref('')
const attachedFiles = ref<File[]>([])
const selectedAssistantId = ref<string | null>(null)
const messagesContainer = ref<HTMLElement>()
const streamingMessageId = ref<string | null>(null)

// Computed
const selectedAssistant = computed(() => {
  if (!selectedAssistantId.value) return null
  return assistantsList.value.find(a => a.id === selectedAssistantId.value) || null
})

// Methods
const handleAssistantSelect = async (assistant: Assistant) => {
  selectedAssistantId.value = assistant.id
  
  // Create a new session with this assistant
  const result = await chatStore.createSession(assistant.id, `Chat with ${assistant.name}`)
  if (result.success) {
    await router.push({ 
      name: 'chat', 
      params: { sessionId: result.data!.id } 
    })
  }
}

const handleNewChat = async () => {
  if (!selectedAssistant.value) return
  
  const result = await chatStore.createSession(
    selectedAssistant.value.id, 
    `Chat with ${selectedAssistant.value.name}`
  )
  
  if (result.success) {
    messageInput.value = ''
    attachedFiles.value = []
    await router.push({ 
      name: 'chat', 
      params: { sessionId: result.data!.id } 
    })
  }
}

const handleSendMessage = async () => {
  if (!messageInput.value.trim() || !currentSession.value) return
  
  const content = messageInput.value.trim()
  const files = attachedFiles.value.length > 0 ? [...attachedFiles.value] : undefined
  
  messageInput.value = ''
  attachedFiles.value = []
  
  // Track the streaming message ID
  streamingMessageId.value = `temp-assistant-${Date.now()}`
  
  await chatStore.sendMessage(content, files)
  
  // Reset streaming message ID when done
  streamingMessageId.value = null
  
  // Scroll to bottom
  await nextTick()
  scrollToBottom()
}

const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleSendMessage()
  }
}

const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files) {
    attachedFiles.value = [...attachedFiles.value, ...Array.from(target.files)]
  }
  target.value = ''
}

const removeFile = (index: number) => {
  attachedFiles.value.splice(index, 1)
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// Watch for new messages to scroll to bottom
watch(() => currentMessages.value.length, () => {
  nextTick(() => scrollToBottom())
})

// Initialize
onMounted(async () => {
  // Initialize WebSocket connection for streaming
  chatStore.initializeWebSocket()
  
  // Load assistants
  await assistantsStore.fetchAssistants()
  
  // If there's a session ID in the route, load it
  const sessionId = route.params.sessionId as string
  if (sessionId) {
    const result = await chatStore.loadSession(sessionId)
    if (result.success && result.data) {
      selectedAssistantId.value = result.data.assistantId
    }
  }
})

// Clean up
onUnmounted(() => {
  // Disconnect WebSocket when component is unmounted
  chatStore.disconnectWebSocket()
})
</script>

<style scoped>
.chat-view {
  /* Custom styles if needed */
}
</style>