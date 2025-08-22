<template>
  <div class="conversation-interface flex flex-col h-full">
    <!-- Header -->
    <div class="flex-none border-b border-gray-200 p-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="p-2 bg-blue-100 rounded-lg">
            <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
            </svg>
          </div>
          <div>
            <h2 class="font-semibold text-gray-900">{{ assistantName }}</h2>
            <p class="text-sm text-gray-500">{{ conversationTitle || 'New Conversation' }}</p>
          </div>
        </div>
        
        <div class="flex items-center space-x-2">
          <!-- Conversation settings -->
          <button
            @click="showSettings = !showSettings"
            class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            title="Conversation Settings"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
            </svg>
          </button>
          
          <!-- Close conversation -->
          <button
            @click="$emit('close')"
            class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            title="Close Conversation"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
      </div>
      
      <!-- Settings Panel -->
      <div v-if="showSettings" class="mt-4 p-4 bg-gray-50 rounded-lg">
        <h3 class="font-medium text-gray-900 mb-3">Conversation Settings</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Title</label>
            <input
              v-model="editableTitle"
              @blur="updateTitle"
              @keyup.enter="updateTitle"
              class="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter conversation title"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Messages</label>
            <p class="text-sm text-gray-500 py-2">{{ messages.length }} messages in conversation</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Thread Control</label>
            <button
              @click="resetThread"
              :disabled="isResettingThread"
              class="w-full px-3 py-2 text-sm bg-orange-100 text-orange-700 border border-orange-300 rounded-md hover:bg-orange-200 focus:outline-none focus:ring-2 focus:ring-orange-500 disabled:opacity-50 transition-colors"
            >
              {{ isResettingThread ? 'Creating...' : 'New Thread' }}
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Messages Area -->
    <div class="flex-1 overflow-hidden flex flex-col">
      <div 
        ref="messagesContainer"
        class="flex-1 overflow-y-auto p-4 space-y-4"
      >
        <!-- Welcome Message -->
        <div v-if="messages.length === 0" class="text-center py-8">
          <div class="p-4 bg-blue-50 border border-blue-200 rounded-lg max-w-md mx-auto">
            <svg class="w-8 h-8 text-blue-500 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
            </svg>
            <p class="text-blue-800 font-medium">Start a conversation</p>
            <p class="text-blue-600 text-sm mt-1">Ask {{ assistantName }} anything to get started.</p>
          </div>
        </div>
        
        <!-- Messages -->
        <ChatMessage
          v-for="message in messages"
          :key="message.id"
          :message="message"
          :is-streaming="isStreaming && message === messages[messages.length - 1] && message.role === 'assistant'"
          :streaming-content="streamingContent"
        />
        
        <!-- Typing indicator -->
        <div v-if="isSending && !isStreaming" class="flex justify-start">
          <div class="flex items-center space-x-2 p-3 bg-gray-100 rounded-lg max-w-xs">
            <div class="flex space-x-1">
              <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
              <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
              <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
            </div>
            <span class="text-sm text-gray-500">{{ assistantName }} is thinking...</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Message Input -->
    <div class="flex-none border-t border-gray-200">
      <!-- Image Upload Area -->
      <div v-if="showImageUpload" class="p-4 border-b border-gray-200 bg-gray-50">
        <ImageUpload
          ref="imageUpload"
          :maxFiles="5"
          :maxFileSize="10 * 1024 * 1024"
          @upload-complete="onImageUploadComplete"
          @upload-error="onImageUploadError"
          @images-changed="onImagesChanged"
        />
      </div>
      
      <div class="p-4">
        <form @submit.prevent="sendMessage" class="relative">
          <div class="flex items-end space-x-2">
            <!-- Image Upload Toggle -->
            <button
              type="button"
              @click="toggleImageUpload"
              :class="[
                'p-2 rounded-lg transition-colors',
                showImageUpload
                  ? 'text-blue-600 bg-blue-100 hover:bg-blue-200'
                  : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
              ]"
              title="Upload images"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
              </svg>
            </button>
            
            <!-- Message Textarea -->
            <div class="flex-1 relative">
              <textarea
                ref="messageInput"
                v-model="newMessage"
                @keydown.enter.exact.prevent="sendMessage"
                @keydown.enter.shift.exact="onShiftEnter"
                :disabled="isSending"
                class="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                :class="{ 'opacity-50 cursor-not-allowed': isSending }"
                :placeholder="uploadedImages.length > 0 ? 'Add a message to your images...' : 'Type your message... (Enter to send, Shift+Enter for new line)'"
                rows="1"
              ></textarea>
              
              <!-- Send Button -->
              <button
                type="submit"
                :disabled="!canSend"
                class="absolute right-2 bottom-2 p-2 text-blue-600 hover:text-blue-700 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors"
                :title="canSend ? 'Send message' : (uploadedImages.length > 0 ? 'Send images' : 'Enter a message to send')"
              >
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z"/>
                </svg>
              </button>
            </div>
            
            <!-- Gallery Toggle -->
            <button
              v-if="hasConversationImages"
              type="button"
              @click="toggleImageGallery"
              class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              title="View conversation images"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
              </svg>
            </button>
          </div>
        </form>
        
        <!-- Error Display -->
        <div v-if="error" class="mt-2 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div class="flex items-center">
            <svg class="w-5 h-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>
            <span class="text-red-800 text-sm">{{ error }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Image Gallery Modal -->
    <div 
      v-if="showGallery"
      class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
      @click="showGallery = false"
    >
      <div
        class="bg-white rounded-lg max-w-4xl max-h-full w-full overflow-hidden"
        @click.stop
      >
        <ImageGallery
          :messages="messages"
          @close="showGallery = false"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { useConversationsStore } from '@/stores/conversations'
import { useAssistantsStore } from '@/stores/assistants'
import { apiClient } from '@/utils/api'
import type { ConversationMessage, Conversation, ImageAttachment } from '@/types'
import ChatMessage from './ChatMessage.vue'
import ImageUpload from './ImageUpload.vue'
import ImageGallery from './ImageGallery.vue'

interface Props {
  conversation: Conversation | null
  messages: ConversationMessage[]
  assistantName: string
}

interface Emits {
  (e: 'close'): void
  (e: 'titleUpdated', title: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const conversationsStore = useConversationsStore()

// State
const newMessage = ref('')
const showSettings = ref(false)
const editableTitle = ref('')
const isResettingThread = ref(false)
const messagesContainer = ref<HTMLElement>()
const messageInput = ref<HTMLTextAreaElement>()
const imageUpload = ref<InstanceType<typeof ImageUpload>>()

// Image-related state
const showImageUpload = ref(false)
const showGallery = ref(false)
const uploadedImages = ref<ImageAttachment[]>([])
const uploadError = ref('')

// Computed
const conversationTitle = computed(() => props.conversation?.title)
const { isSending, error, streamingContent, isStreaming } = conversationsStore

const canSend = computed(() => {
  return (newMessage.value.trim().length > 0 || uploadedImages.value.length > 0) && !isSending.value
})

const hasConversationImages = computed(() => {
  return props.messages.some(message => message.attachments && message.attachments.length > 0)
})

// Methods
const sendMessage = async () => {
  if (!canSend.value || !props.conversation) return
  
  const content = newMessage.value.trim()
  const attachments = [...uploadedImages.value]
  
  // Clear inputs
  newMessage.value = ''
  uploadedImages.value = []
  
  // Clear upload component
  if (imageUpload.value) {
    imageUpload.value.clearImages()
  }
  
  // Auto-resize textarea
  if (messageInput.value) {
    messageInput.value.style.height = 'auto'
  }
  
  // Get the last assistant message's response_id for conversation continuity
  const lastAssistantMessage = [...props.messages]
    .reverse()
    .find(m => m.role === 'assistant')
  
  await conversationsStore.sendMessage(
    content,
    props.conversation.assistant_id,
    lastAssistantMessage?.response_id,
    attachments.length > 0 ? attachments : undefined
  )
  
  // Scroll to bottom after sending
  await nextTick()
  scrollToBottom()
}

const onShiftEnter = () => {
  // Allow default behavior for Shift+Enter (new line)
  return
}

const resetThread = async () => {
  if (!props.conversation || isResettingThread.value) return
  
  isResettingThread.value = true
  
  try {
    // Get the assistant from the conversation to get the OpenAI assistant ID
    const assistantsStore = useAssistantsStore()
    const assistant = assistantsStore.getAssistantById.value(props.conversation.assistant_id)
    
    if (assistant) {
      // Call the new-thread endpoint with the OpenAI assistant ID
      const response = await apiClient.post('/chat/new-thread', {
        assistant_id: assistant.assistant_id
      })
      
      if (response.success) {
        // Clear current messages to show fresh thread
        conversationsStore.clearCurrentConversation()
        
        // Reload the conversation to get fresh state
        await conversationsStore.loadConversation(props.conversation.id)
        
        console.log('New thread created successfully')
      } else {
        console.error('Failed to create new thread:', response.error)
      }
    }
  } catch (error) {
    console.error('Error creating new thread:', error)
  } finally {
    isResettingThread.value = false
  }
}

const updateTitle = async () => {
  if (!props.conversation || editableTitle.value === conversationTitle.value) return
  
  const result = await conversationsStore.updateConversationTitle(
    props.conversation.id,
    editableTitle.value
  )
  
  if (result.success) {
    emit('titleUpdated', editableTitle.value)
  } else {
    // Reset to original title on error
    editableTitle.value = conversationTitle.value || ''
  }
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const autoResizeTextarea = () => {
  if (messageInput.value) {
    messageInput.value.style.height = 'auto'
    messageInput.value.style.height = Math.min(messageInput.value.scrollHeight, 120) + 'px'
  }
}

// Image-related methods
const toggleImageUpload = () => {
  showImageUpload.value = !showImageUpload.value
  if (!showImageUpload.value) {
    // Clear uploaded images when closing upload area
    uploadedImages.value = []
    if (imageUpload.value) {
      imageUpload.value.clearImages()
    }
  }
}

const toggleImageGallery = () => {
  showGallery.value = !showGallery.value
}

const onImageUploadComplete = (images: ImageAttachment[]) => {
  console.log('Images uploaded:', images)
}

const onImageUploadError = (error: string) => {
  uploadError.value = error
  // Clear error after 5 seconds
  setTimeout(() => {
    uploadError.value = ''
  }, 5000)
}

const onImagesChanged = (images: ImageAttachment[]) => {
  uploadedImages.value = images
}

// Watch for new messages and scroll to bottom
watch(() => props.messages.length, async () => {
  await nextTick()
  scrollToBottom()
})

// Watch for streaming content and scroll to bottom
watch(streamingContent, async () => {
  await nextTick()
  scrollToBottom()
})

// Watch conversation title changes
watch(conversationTitle, (newTitle) => {
  editableTitle.value = newTitle || ''
})

// Auto-resize textarea on input
watch(newMessage, () => {
  nextTick(autoResizeTextarea)
})

// Initialize
onMounted(() => {
  editableTitle.value = conversationTitle.value || ''
  if (messageInput.value) {
    messageInput.value.focus()
  }
})

// Cleanup WebSocket connections on unmount
onUnmounted(() => {
  if (props.conversation) {
    conversationsStore.disconnectConversationWebSocket(props.conversation.id)
  }
})
</script>

<style scoped>
/* Custom scrollbar for messages container */
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: #f1f5f9;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* Textarea auto-resize */
textarea {
  max-height: 120px;
  min-height: 44px;
}

/* Typing animation */
@keyframes bounce {
  0%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-6px);
  }
}

.animate-bounce {
  animation: bounce 1.4s infinite;
}
</style>