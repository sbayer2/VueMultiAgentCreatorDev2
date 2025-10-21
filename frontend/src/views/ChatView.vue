<template>
  <div class="chat-view h-screen flex bg-gray-50">
    <!-- Assistants Sidebar -->
    <aside
      :class="[
        'bg-white border-r border-gray-200 flex flex-col transition-all duration-300',
        assistantsSidebarCollapsed ? 'w-0 overflow-hidden' : 'w-80'
      ]"
    >
      <!-- Header -->
      <div class="p-4 border-b border-gray-200">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-semibold text-gray-900">Assistants</h2>
          <router-link
            to="/dashboard/assistants"
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

      <!-- Assistants List -->
      <div class="flex-1 overflow-y-auto">
        <div v-if="assistantsList.length === 0" class="p-4 text-center text-gray-500">
          <p class="text-sm">No assistants available.</p>
          <router-link to="/dashboard/assistants/create" class="text-sm text-blue-600 hover:underline">
            Create one now
          </router-link>
        </div>
        
        <div v-else class="space-y-1 p-2">
          <button
            v-for="assistant in assistantsList"
            :key="assistant.id"
            @click="selectAssistant(assistant)"
            class="w-full text-left p-3 rounded-lg hover:bg-gray-50 transition-colors"
            :class="{ 'bg-blue-50': assistant.id === activeAssistant?.id }"
          >
            <p class="text-sm font-medium text-gray-900 truncate">{{ assistant.name }}</p>
            <p class="text-xs text-gray-500 mt-1">{{ assistant.model }}</p>
          </button>
        </div>
      </div>
    </aside>

    <!-- Main Chat Area -->
    <main class="flex-1 flex flex-col relative">
      <!-- Toggle Button for Assistants Sidebar -->
      <button
        @click="toggleAssistantsSidebar"
        :class="[
          'absolute left-2 top-2 z-10 p-2 rounded-lg bg-white shadow-md hover:shadow-lg transition-all duration-200',
          'text-gray-600 hover:text-gray-900'
        ]"
        :title="assistantsSidebarCollapsed ? 'Show Assistants' : 'Hide Assistants'"
      >
        <svg v-if="assistantsSidebarCollapsed" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
        <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>

      <div v-if="!activeAssistant" class="flex-1 flex items-center justify-center">
        <div class="text-center">
          <svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
          </svg>
          <h3 class="text-xl font-semibold text-gray-900 mb-2">Select an Assistant</h3>
          <p class="text-gray-600 max-w-md">
            Choose an assistant from the sidebar to start a conversation.
          </p>
        </div>
      </div>
      
      <ConversationInterface
        v-else
        :key="activeAssistant.id"
        :conversation="null" 
        :messages="activeThreadMessages"
        :assistant-name="activeAssistant.name"
        @close="conversationsStore.clearCurrentConversation()"
      />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute, useRouter } from 'vue-router'
import { useAssistantsStore } from '@/stores/assistants'
import { useConversationsStore } from '@/stores/conversations'
import ConversationInterface from '@/components/chat/ConversationInterface.vue'
import type { Assistant } from '@/types'

const route = useRoute()
const router = useRouter()
const assistantsStore = useAssistantsStore()
const conversationsStore = useConversationsStore()

// Sidebar state
const assistantsSidebarCollapsed = ref(false)

// Store data with reactivity
const { assistantsList } = storeToRefs(assistantsStore)
const { activeAssistant, activeThreadMessages } = storeToRefs(conversationsStore)

// Methods
const selectAssistant = async (assistant: Assistant) => {
  await conversationsStore.selectAssistantForChat(assistant)
  // Update URL to reflect the selected assistant, which now represents the "conversation"
  router.replace({ name: 'chat', params: { conversationId: assistant.id.toString() } })
}

// Toggle assistants sidebar
const toggleAssistantsSidebar = () => {
  assistantsSidebarCollapsed.value = !assistantsSidebarCollapsed.value
  localStorage.setItem('assistantsSidebarCollapsed', String(assistantsSidebarCollapsed.value))
}

// Initialize
onMounted(async () => {
  // Load sidebar state from localStorage
  const savedState = localStorage.getItem('assistantsSidebarCollapsed')
  if (savedState !== null) {
    assistantsSidebarCollapsed.value = savedState === 'true'
  }

  await assistantsStore.fetchAssistants()
  
  // If there's an ID in the route, treat it as an assistant ID and select it
  const assistantIdFromRoute = route.params.conversationId as string
  if (assistantIdFromRoute) {
    const id = parseInt(assistantIdFromRoute, 10)
    if (!isNaN(id)) {
      const assistant = assistantsStore.getAssistantById(id)
      if (assistant) {
        selectAssistant(assistant)
      }
    }
  }
})
</script>