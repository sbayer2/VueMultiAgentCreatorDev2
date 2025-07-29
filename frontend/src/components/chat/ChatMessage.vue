<template>
  <div 
    :class="[
      'chat-message flex',
      message.role === 'user' ? 'justify-end' : 'justify-start'
    ]"
  >
    <div 
      :class="[
        'max-w-2xl px-4 py-2 rounded-lg',
        message.role === 'user' 
          ? 'bg-indigo-600 text-white' 
          : 'bg-gray-100 text-gray-900'
      ]"
    >
      <!-- Message Header -->
      <div class="flex items-center justify-between mb-1">
        <span :class="[
          'text-xs font-medium',
          message.role === 'user' ? 'text-indigo-200' : 'text-gray-500'
        ]">
          {{ message.role === 'user' ? 'You' : 'Assistant' }}
        </span>
        <time 
          :datetime="message.timestamp" 
          :class="[
            'text-xs',
            message.role === 'user' ? 'text-indigo-200' : 'text-gray-400'
          ]"
        >
          {{ formatTime(message.timestamp) }}
        </time>
      </div>

      <!-- Message Content -->
      <div class="prose prose-sm max-w-none">
        <div v-if="isStreaming && streamingContent" class="message-content">
          <span v-html="renderContent(streamingContent)"></span>
          <span class="inline-block w-1 h-4 bg-current animate-pulse ml-1"></span>
        </div>
        <div v-else class="message-content" v-html="renderContent(message.content)"></div>
      </div>

      <!-- File Attachments -->
      <div v-if="message.metadata?.files && message.metadata.files.length > 0" class="mt-2 space-y-1">
        <div 
          v-for="file in message.metadata.files" 
          :key="file.id"
          :class="[
            'inline-flex items-center space-x-1 px-2 py-1 rounded text-xs',
            message.role === 'user' 
              ? 'bg-indigo-700 text-indigo-200' 
              : 'bg-gray-200 text-gray-600'
          ]"
        >
          <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
          </svg>
          <span>{{ file.name }}</span>
          <span v-if="file.size" class="opacity-75">({{ formatFileSize(file.size) }})</span>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="message.role === 'assistant' && !message.content && !isStreaming" class="flex items-center space-x-2">
        <div class="flex space-x-1">
          <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
          <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
          <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Message } from '@/types'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

// Props
const props = defineProps<{
  message: Message
  isStreaming?: boolean
  streamingContent?: string
}>()

// Configure marked with syntax highlighting
marked.setOptions({
  highlight: function(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(code, { language: lang }).value
      } catch (err) {
        console.error('Highlight error:', err)
      }
    }
    return code
  },
  breaks: true,
  gfm: true
})

// Methods
const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  
  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`
  
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
  })
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const renderContent = (content: string) => {
  // Check if content contains code blocks
  if (content.includes('```')) {
    return marked(content)
  }
  
  // For simple text, just convert newlines to breaks
  return content.replace(/\n/g, '<br>')
}
</script>

<style scoped>
.chat-message {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Prose styling overrides */
:deep(.prose) {
  color: inherit;
}

:deep(.prose pre) {
  background-color: #1f2937;
  color: #e5e7eb;
  padding: 1rem;
  border-radius: 0.375rem;
  overflow-x: auto;
}

:deep(.prose code) {
  background-color: rgba(0, 0, 0, 0.1);
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-size: 0.875em;
}

:deep(.prose pre code) {
  background-color: transparent;
  padding: 0;
}

/* Animation for typing indicator */
@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(1);
    opacity: 0.5;
  }
  40% {
    transform: scale(1.3);
    opacity: 1;
  }
}
</style>