<template>
  <div class="chat-view h-screen flex bg-gray-50">
    <!-- Conversations Sidebar -->
    <aside class="w-80 bg-white border-r border-gray-200 flex flex-col">
      <!-- Header -->
      <div class="p-4 border-b border-gray-200">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-semibold text-gray-900">Conversations</h2>
          <router-link
            to="/assistants"
            class="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
            title="Manage Assistants"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
            </svg>
          </router-link>
        </div>
      </div>
      
      <!-- New Conversation Button -->
      <div class="p-4 border-b border-gray-200">
        <button
          @click="showAssistantSelector = true"
          class="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
        >
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
          New Conversation
        </button>
      </div>

      <!-- Conversations List -->
      <div class="flex-1 overflow-y-auto">
        <div v-if="conversationsList.length === 0" class="p-4 text-center text-gray-500">
          <svg class="w-8 h-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
          </svg>
          <p class="text-sm">No conversations yet</p>
          <p class="text-xs text-gray-400 mt-1">Create your first chat</p>
        </div>
        
        <div v-else class="space-y-1 p-2">
          <button
            v-for="conversation in conversationsList"
            :key="conversation.id"
            @click="selectConversation(conversation)"
            class="w-full text-left p-3 rounded-lg hover:bg-gray-50 transition-colors"
            :class="{ 'bg-blue-50 border-blue-200': conversation.id === currentConversation?.id }"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-900 truncate">
                  {{ conversation.title || 'New Conversation' }}
                </p>
                <p class="text-xs text-gray-500 mt-1">
                  {{ getAssistantName(conversation.assistant_id) }} • {{ conversation.message_count }} messages
                </p>
              </div>
              <button
                @click.stop="deleteConversation(conversation)"
                class="p-1 text-gray-400 hover:text-red-500 rounded"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                </svg>
              </button>
            </div>
          </button>
        </div>
      </div>
    </aside>

    <!-- Main Chat Area -->
    <main class="flex-1 flex flex-col">
      <div v-if="!currentConversation" class="flex-1 flex items-center justify-center">
        <div class="text-center">
          <svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
          </svg>
          <h3 class="text-xl font-semibold text-gray-900 mb-2">Welcome to AI Chat</h3>
          <p class="text-gray-600 mb-6 max-w-md">
            Select an existing conversation from the sidebar or create a new one to get started.
          </p>
          <button
            @click="showAssistantSelector = true"
            class="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
            </svg>
            Start New Conversation
          </button>
        </div>
      </div>
      
      <ConversationInterface
        v-else
        :conversation="currentConversation"
        :messages="currentMessages"
        :assistant-name="currentAssistantName"
        @close="currentConversation = null"
        @title-updated="handleTitleUpdated"
      />
    </main>

    <!-- Assistant Selector Modal -->
    <div
      v-if="showAssistantSelector"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="showAssistantSelector = false"
    >
      <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4 max-h-96 overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900">Choose Assistant</h3>
          <button
            @click="showAssistantSelector = false"
            class="text-gray-400 hover:text-gray-600"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        
        <div v-if="assistantsList.length === 0" class="text-center py-8">
          <p class="text-gray-500 mb-4">No assistants available</p>
          <router-link
            to="/assistants/create"
            class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Create Assistant
          </router-link>
        </div>
        
        <div v-else class="space-y-3">
          <button
            v-for="assistant in assistantsList"
            :key="assistant.id"
            @click="createConversationWithAssistant(assistant)"
            class="w-full text-left p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <div class="flex items-center justify-between">
              <div>
                <h4 class="font-medium text-gray-900">{{ assistant.name }}</h4>
                <p v-if="assistant.description" class="text-sm text-gray-600 mt-1">
                  {{ assistant.description }}
                </p>
                <p class="text-xs text-gray-500 mt-1">{{ assistant.model }}</p>
              </div>
              <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
              </svg>
            </div>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute, useRouter } from 'vue-router'
import { useAssistantsStore } from '@/stores/assistants'
import { useConversationsStore } from '@/stores/conversations'
import ConversationInterface from '@/components/chat/ConversationInterface.vue'
import type { Assistant, Conversation } from '@/types'

const route = useRoute()
const router = useRouter()
const assistantsStore = useAssistantsStore()
const conversationsStore = useConversationsStore()

// State
const showAssistantSelector = ref(false)

// Store data with reactivity
const { assistantsList } = storeToRefs(assistantsStore)
const { 
  conversationsList,
  currentConversation,
  currentMessages
} = storeToRefs(conversationsStore)

// Computed
const currentAssistantName = computed(() => {
  if (!currentConversation.value) return ''
  const assistant = assistantsList.value.find(a => a.id === currentConversation.value!.assistant_id)
  return assistant?.name || 'Unknown Assistant'
})

// Methods
const selectConversation = async (conversation: Conversation) => {
  const result = await conversationsStore.loadConversation(conversation.id)
  
  if (result.success) {
    // Update URL without page reload
    await router.replace({ 
      name: 'chat', 
      params: { conversationId: conversation.id.toString() } 
    })
  }
}

const createConversationWithAssistant = async (assistant: Assistant) => {
  showAssistantSelector.value = false
  
  const result = await conversationsStore.createConversation({
    assistant_id: assistant.id,
    title: `Chat with ${assistant.name}`
  })
  
  if (result.success && result.data) {
    // Update URL to reflect the new conversation
    await router.push({ 
      name: 'chat', 
      params: { conversationId: result.data.id.toString() } 
    })
  }
}

const deleteConversation = async (conversation: Conversation) => {
  if (confirm(`Are you sure you want to delete this conversation? This action cannot be undone.`)) {
    const result = await conversationsStore.deleteConversation(conversation.id)
    
    if (result.success) {
      // If this was the current conversation, clear it
      if (currentConversation.value?.id === conversation.id) {
        await router.replace({ name: 'chat' })
      }
    }
  }
}

const getAssistantName = (assistantId: number): string => {
  const assistant = assistantsList.find(a => a.id === assistantId)
  return assistant?.name || 'Unknown Assistant'
}

const handleTitleUpdated = async (newTitle: string) => {
  // The title is already updated in the store by the ConversationInterface
  // We could add additional logic here if needed
}

// Initialize
onMounted(async () => {
  // Initialize WebSocket connection for streaming
  conversationsStore.initializeWebSocket()
  
  // Load assistants and conversations
  await Promise.all([
    assistantsStore.fetchAssistants(),
    conversationsStore.fetchConversations()
  ])
  
  // If there's a conversation ID in the route, load it
  const conversationId = route.params.conversationId as string
  if (conversationId) {
    const id = parseInt(conversationId, 10)
    if (!isNaN(id)) {
      await conversationsStore.loadConversation(id)
    }
  }
})

// Clean up
onUnmounted(() => {
  // Disconnect WebSocket when component is unmounted
  conversationsStore.disconnectWebSocket()
})
</script>

<style scoped>
.chat-view {
  /* Custom styles if needed */
}
</style>