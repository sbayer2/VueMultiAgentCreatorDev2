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
          :datetime="message.created_at" 
          :class="[
            'text-xs',
            message.role === 'user' ? 'text-indigo-200' : 'text-gray-400'
          ]"
        >
          {{ formatTime(message.created_at) }}
        </time>
      </div>

      <!-- Message Content -->
      <div class="space-y-2">
        <!-- Image Attachments -->
        <div v-if="imageAttachments.length > 0" class="mb-2">
          <ImageDisplay :images="imageAttachments" :maxWidth="300" :maxHeight="200" />
        </div>
        
        <!-- Text Content -->
        <div v-if="message.content" class="prose prose-sm max-w-none">
          <div v-if="isStreaming && streamingContent" class="message-content">
            <span v-html="renderContent(streamingContent)"></span>
            <span class="inline-block w-1 h-4 bg-current animate-pulse ml-1"></span>
          </div>
          <div v-else class="message-content" v-html="renderContent(message.content)"></div>
        </div>

        <!-- Non-Image File Attachments -->
        <div v-if="nonImageAttachments.length > 0" class="mt-2 border-t pt-2">
          <p class="text-xs font-medium text-gray-500 mb-1">Referenced Files:</p>
          <div class="space-y-1">
            <div v-for="file in nonImageAttachments" :key="file.id" class="flex items-center space-x-2">
              <svg class="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
              <span class="text-xs text-gray-600 truncate">{{ file.name }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Tool Calls Display -->
      <div v-if="message.tool_calls && message.tool_calls.length > 0" class="mt-2 space-y-1">
        <div 
          v-for="toolCall in message.tool_calls" 
          :key="toolCall.id"
          :class="[
            'inline-flex items-center space-x-1 px-2 py-1 rounded text-xs',
            'bg-blue-100 text-blue-800 border border-blue-200'
          ]"
        >
          <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
          </svg>
          <span>{{ toolCall.function?.name || toolCall.type }}</span>
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
import type { ConversationMessage } from '@/types'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import ImageDisplay from './ImageDisplay.vue'

// Props
const props = defineProps<{
  message: ConversationMessage
  isStreaming?: boolean
  streamingContent?: string
}>()

const imageAttachments = computed(() => 
  props.message.attachments?.filter(att => att.type.startsWith('image/')) ?? []
);

const nonImageAttachments = computed(() => 
  props.message.attachments?.filter(att => !att.type.startsWith('image/')) ?? []
);


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