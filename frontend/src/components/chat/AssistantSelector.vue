<template>
  <div class="assistant-selector flex-1 overflow-y-auto">
    <!-- Loading State -->
    <div v-if="isLoading" class="p-4">
      <div class="animate-pulse space-y-3">
        <div v-for="i in 3" :key="i" class="bg-gray-200 h-20 rounded-lg"></div>
      </div>
    </div>

    <!-- Assistants List -->
    <div v-else-if="assistants.length > 0" class="p-4 space-y-3">
      <button
        v-for="assistant in assistants"
        :key="assistant.id"
        @click="$emit('select', assistant)"
        :class="[
          'w-full text-left p-4 rounded-lg border transition-all duration-200',
          selectedAssistantId === assistant.id
            ? 'border-indigo-500 bg-indigo-50 ring-2 ring-indigo-500'
            : 'border-gray-200 hover:border-gray-300 hover:shadow-sm bg-white'
        ]"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1 min-w-0">
            <div class="flex items-center space-x-2">
              <h3 :class="[
                'text-sm font-medium truncate',
                selectedAssistantId === assistant.id ? 'text-indigo-900' : 'text-gray-900'
              ]">
                {{ assistant.name }}
              </h3>
              <span 
                v-if="isAssistantOnline(assistant.id)"
                class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
              >
                <span class="w-1.5 h-1.5 bg-green-400 rounded-full mr-1 animate-pulse"></span>
                Active
              </span>
            </div>
            <p :class="[
              'mt-1 text-xs truncate',
              selectedAssistantId === assistant.id ? 'text-indigo-700' : 'text-gray-500'
            ]">
              {{ assistant.description }}
            </p>
            <div class="mt-2 flex items-center space-x-3 text-xs">
              <span :class="[
                'inline-flex items-center',
                selectedAssistantId === assistant.id ? 'text-indigo-600' : 'text-gray-400'
              ]">
                <svg class="mr-1 h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                {{ assistant.model }}
              </span>
              <span :class="[
                'inline-flex items-center',
                selectedAssistantId === assistant.id ? 'text-indigo-600' : 'text-gray-400'
              ]">
                <svg class="mr-1 h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
                {{ assistant.files.length }} files
              </span>
            </div>
          </div>
          <div v-if="selectedAssistantId === assistant.id" class="ml-2 flex-shrink-0">
            <svg class="h-5 w-5 text-indigo-600" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
          </div>
        </div>
      </button>
    </div>

    <!-- Empty State -->
    <div v-else class="p-4 text-center">
      <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-gray-900">No assistants</h3>
      <p class="mt-1 text-sm text-gray-500">Create an assistant to get started</p>
      <div class="mt-6">
        <router-link
          to="/assistants/new"
          class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          <svg class="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          New Assistant
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import type { Assistant } from '@/types'

// Props
const props = defineProps<{
  assistants: Assistant[]
  selectedAssistantId: string | null
  isLoading: boolean
}>()

// Emits
const emit = defineEmits<{
  select: [assistant: Assistant]
}>()

// Local state for online status (mock implementation)
const onlineAssistants = ref<Set<string>>(new Set())

// Methods
const isAssistantOnline = (assistantId: string) => {
  return onlineAssistants.value.has(assistantId)
}

// Mock WebSocket connection for online status
let ws: WebSocket | null = null

const connectWebSocket = () => {
  // In a real implementation, this would connect to your WebSocket server
  // For now, we'll simulate random online status changes
  
  // Simulate some assistants being online
  if (props.assistants.length > 0) {
    const randomOnline = props.assistants
      .slice(0, Math.ceil(props.assistants.length / 2))
      .map(a => a.id)
    onlineAssistants.value = new Set(randomOnline)
  }
  
  // Simulate status changes
  const interval = setInterval(() => {
    if (props.assistants.length > 0) {
      const randomAssistant = props.assistants[Math.floor(Math.random() * props.assistants.length)]
      if (onlineAssistants.value.has(randomAssistant.id)) {
        onlineAssistants.value.delete(randomAssistant.id)
      } else {
        onlineAssistants.value.add(randomAssistant.id)
      }
      // Force reactivity
      onlineAssistants.value = new Set(onlineAssistants.value)
    }
  }, 10000) // Change status every 10 seconds
  
  return () => clearInterval(interval)
}

// Lifecycle
onMounted(() => {
  const cleanup = connectWebSocket()
  
  // Store cleanup function
  onUnmounted(() => {
    cleanup()
    if (ws) {
      ws.close()
    }
  })
})
</script>

<style scoped>
.assistant-selector {
  /* Custom scrollbar styling */
  scrollbar-width: thin;
  scrollbar-color: #e5e7eb #f9fafb;
}

.assistant-selector::-webkit-scrollbar {
  width: 6px;
}

.assistant-selector::-webkit-scrollbar-track {
  background: #f9fafb;
}

.assistant-selector::-webkit-scrollbar-thumb {
  background-color: #e5e7eb;
  border-radius: 3px;
}

.assistant-selector::-webkit-scrollbar-thumb:hover {
  background-color: #d1d5db;
}
</style>