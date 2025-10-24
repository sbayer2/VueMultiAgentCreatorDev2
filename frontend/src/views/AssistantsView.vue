<template>
  <div class="assistants-view max-w-7xl mx-auto px-4 py-6">
    <!-- Header -->
    <div class="mb-8">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Your Assistants</h1>
          <p class="text-gray-600 mt-2">
            Create and manage your AI assistants with custom instructions and tools
          </p>
        </div>
        
        <router-link
          to="/dashboard/assistants/create"
          class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
        >
          <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
          Create Assistant
        </router-link>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading && assistantsList.length === 0" class="text-center py-12">
      <LoadingSpinner size="large" />
      <p class="text-gray-500 mt-4">Loading your assistants...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error && assistantsList.length === 0" class="text-center py-12">
      <div class="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md mx-auto">
        <svg class="w-8 h-8 text-red-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 15.5c-.77.833.192 2.5 1.732 2.5z"/>
        </svg>
        <h3 class="text-lg font-medium text-red-800 mb-2">Failed to Load Assistants</h3>
        <p class="text-red-600 mb-4">{{ error }}</p>
        <button
          @click="handleRefresh"
          class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
        >
          Try Again
        </button>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="assistantsList.length === 0 && !isLoading" class="text-center py-12">
      <div class="bg-gray-50 border border-gray-200 rounded-lg p-8 max-w-md mx-auto">
        <svg class="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
        </svg>
        <h3 class="text-lg font-medium text-gray-900 mb-2">No Assistants Yet</h3>
        <p class="text-gray-500 mb-6">
          Get started by creating your first AI assistant with custom instructions and tools.
        </p>
        <router-link
          to="/dashboard/assistants/create"
          class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
          Create Your First Assistant
        </router-link>
      </div>
    </div>

    <!-- Assistants Grid -->
    <div v-else class="space-y-6">
      <!-- Stats -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="bg-white rounded-lg border border-gray-200 p-6">
          <div class="flex items-center">
            <div class="p-2 bg-blue-100 rounded-lg">
              <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
              </svg>
            </div>
            <div class="ml-4">
              <p class="text-2xl font-semibold text-gray-900">{{ assistantsCount }}</p>
              <p class="text-gray-500">Total Assistants</p>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-gray-200 p-6">
          <div class="flex items-center">
            <div class="p-2 bg-green-100 rounded-lg">
              <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
            </div>
            <div class="ml-4">
              <p class="text-2xl font-semibold text-gray-900">{{ activeAssistants }}</p>
              <p class="text-gray-500">Active Assistants</p>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-gray-200 p-6">
          <div class="flex items-center">
            <div class="p-2 bg-purple-100 rounded-lg">
              <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/>
              </svg>
            </div>
            <div class="ml-4">
              <p class="text-2xl font-semibold text-gray-900">{{ enabledToolsCount }}</p>
              <p class="text-gray-500">Tools Enabled</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Assistants List -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="assistant in assistantsList"
          :key="assistant.id"
          class="bg-white rounded-lg border border-gray-200 hover:shadow-lg transition-shadow duration-200 overflow-hidden"
        >
          <!-- Assistant Card Header -->
          <div class="p-6 pb-4">
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <h3 class="text-lg font-semibold text-gray-900 mb-2">{{ assistant.name }}</h3>
                <p v-if="assistant.description" class="text-gray-600 text-sm mb-3">{{ assistant.description }}</p>
                
                <!-- Model Badge -->
                <div class="flex items-center mb-3">
                  <span class="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded-full">
                    {{ assistant.model }}
                  </span>
                </div>
              </div>
              
              <!-- Actions Dropdown -->
              <div class="relative" ref="dropdownRef">
                <button
                  @click="toggleDropdown(assistant.id)"
                  class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"/>
                  </svg>
                </button>
                
                <div
                  v-if="activeDropdown === assistant.id"
                  class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-20"
                >
                  <div class="py-1">
                    <button
                      @click.stop="startChat(assistant)"
                      class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center"
                    >
                      <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                      </svg>
                      Start Chat
                    </button>
                    <router-link
                      :to="`/dashboard/assistants/${assistant.assistant_id}/edit`"
                      class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center"
                    >
                      <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                      </svg>
                      Edit
                    </router-link>
                    <button
                      @click.stop="confirmDelete(assistant)"
                      class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center"
                    >
                      <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                      </svg>
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Tools Display -->
          <div class="px-6 pb-4">
            <div class="flex flex-wrap gap-2">
              <span
                v-if="assistant.tools.web_search"
                class="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded-full"
              >
                Web Search
              </span>
              <span
                v-if="assistant.tools.file_search"
                class="px-2 py-1 text-xs bg-green-100 text-green-700 rounded-full"
              >
                File Search
              </span>
              <span
                v-if="assistant.tools.code_interpreter"
                class="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded-full"
              >
                Code Interpreter
              </span>
              <span
                v-if="assistant.tools.computer_use"
                class="px-2 py-1 text-xs bg-orange-100 text-orange-700 rounded-full"
              >
                Computer Use
              </span>
            </div>
          </div>

          <!-- Card Footer -->
          <div class="px-6 py-4 bg-gray-50 border-t border-gray-200">
            <div class="flex items-center justify-between text-sm">
              <div class="flex items-center gap-2">
                <span
                  v-if="assistant.conversation_count > 0"
                  class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
                >
                  <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                  </svg>
                  Active
                </span>
                <span
                  v-else
                  class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600"
                >
                  <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm0-2a6 6 0 100-12 6 6 0 000 12z" clip-rule="evenodd"/>
                  </svg>
                  Not Started
                </span>
              </div>
              <span class="text-gray-500">{{ formatDate(assistant.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div
      v-if="assistantToDelete"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="assistantToDelete = null"
    >
      <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <div class="flex items-center mb-4">
          <div class="p-2 bg-red-100 rounded-lg mr-3">
            <svg class="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 15.5c-.77.833.192 2.5 1.732 2.5z"/>
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-gray-900">Delete Assistant</h3>
        </div>
        
        <p class="text-gray-600 mb-6">
          Are you sure you want to delete "{{ assistantToDelete.name }}"? This will also delete all associated conversations. This action cannot be undone.
        </p>
        
        <div class="flex space-x-3">
          <button
            @click="assistantToDelete = null"
            class="flex-1 px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            Cancel
          </button>
          <button
            @click="handleDelete"
            :disabled="isDeleting"
            class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
          >
            {{ isDeleting ? 'Deleting...' : 'Delete' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAssistantsStore } from '@/stores/assistants'
import { useConversationsStore } from '@/stores/conversations'
import type { Assistant } from '@/types'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const router = useRouter()
const assistantsStore = useAssistantsStore()
const conversationsStore = useConversationsStore()

// State
const activeDropdown = ref<number | null>(null)
const assistantToDelete = ref<Assistant | null>(null)
const isDeleting = ref(false)

// Computed
const { assistantsList, assistantsCount, isLoading, error } = assistantsStore
const activeAssistants = computed(() =>
  assistantsList.filter(assistant => assistant.conversation_count > 0).length
)
const enabledToolsCount = computed(() => {
  return assistantsList.reduce((count, assistant) => {
    const tools = assistant.tools
    return count + 
      (tools.web_search ? 1 : 0) +
      (tools.file_search ? 1 : 0) +
      (tools.code_interpreter ? 1 : 0) +
      (tools.computer_use ? 1 : 0)
  }, 0)
})

// Methods
const handleRefresh = async () => {
  await assistantsStore.fetchAssistants()
}

const toggleDropdown = (assistantId: number) => {
  activeDropdown.value = activeDropdown.value === assistantId ? null : assistantId
}

const startChat = (assistant: Assistant) => {
  activeDropdown.value = null
  conversationsStore.selectAssistantForChat(assistant)
  router.push({ 
    name: 'chat', 
    params: { conversationId: assistant.id.toString() } 
  })
}

const confirmDelete = (assistant: Assistant) => {
  assistantToDelete.value = assistant
  activeDropdown.value = null
}

const handleDelete = async () => {
  if (!assistantToDelete.value) return
  
  isDeleting.value = true
  
  try {
    const result = await assistantsStore.deleteAssistant(assistantToDelete.value.assistant_id)
    
    if (result.success) {
      assistantToDelete.value = null
    } else {
      console.error('Failed to delete assistant:', result.error)
    }
  } catch (error) {
    console.error('Unexpected error:', error)
  } finally {
    isDeleting.value = false
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

// Close dropdown when clicking outside
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as Element
  if (!target.closest('.relative')) {
    activeDropdown.value = null
  }
}

// Lifecycle
onMounted(async () => {
  await assistantsStore.fetchAssistants()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
/* Custom animation for dropdown */
.relative > div {
  animation: fadeInScale 0.15s ease-out;
}

@keyframes fadeInScale {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* Hover effects */
.hover\:shadow-lg {
  transition: box-shadow 0.2s ease-in-out;
}
</style>