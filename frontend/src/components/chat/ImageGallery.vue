<template>
  <div class="image-gallery">
    <!-- Gallery Header -->
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-medium text-gray-900">
        Conversation Images
        <span v-if="allImages.length > 0" class="text-sm font-normal text-gray-500 ml-2">
          ({{ allImages.length }})
        </span>
      </h3>
      
      <div class="flex items-center space-x-2">
        <!-- View Toggle -->
        <div class="flex bg-gray-100 rounded-lg p-1">
          <button
            @click="viewMode = 'grid'"
            :class="[
              'px-3 py-1 text-sm rounded-md transition-colors duration-200',
              viewMode === 'grid'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            ]"
          >
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/>
            </svg>
          </button>
          <button
            @click="viewMode = 'list'"
            :class="[
              'px-3 py-1 text-sm rounded-md transition-colors duration-200',
              viewMode === 'list'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            ]"
          >
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"/>
            </svg>
          </button>
        </div>
        
        <!-- Close Button -->
        <button
          @click="$emit('close')"
          class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>
    </div>
    
    <!-- Search and Filter -->
    <div v-if="allImages.length > 0" class="mb-4 space-y-3">
      <!-- Search Input -->
      <div class="relative">
        <svg class="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search images by name..."
          class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>
      
      <!-- Filters -->
      <div class="flex items-center space-x-4">
        <!-- Date Filter -->
        <select
          v-model="dateFilter"
          class="px-3 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All dates</option>
          <option value="today">Today</option>
          <option value="week">This week</option>
          <option value="month">This month</option>
        </select>
        
        <!-- Type Filter -->
        <select
          v-model="typeFilter"
          class="px-3 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All types</option>
          <option value="image/jpeg">JPEG</option>
          <option value="image/png">PNG</option>
          <option value="image/gif">GIF</option>
          <option value="image/webp">WebP</option>
        </select>
        
        <!-- Sort Order -->
        <select
          v-model="sortOrder"
          class="px-3 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="newest">Newest first</option>
          <option value="oldest">Oldest first</option>
          <option value="largest">Largest first</option>
          <option value="smallest">Smallest first</option>
          <option value="name">Name A-Z</option>
        </select>
      </div>
    </div>
    
    <!-- Gallery Content -->
    <div class="gallery-content">
      <!-- Empty State -->
      <div v-if="allImages.length === 0" class="text-center py-12">
        <svg class="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
        </svg>
        <h4 class="text-lg font-medium text-gray-900 mb-2">No images yet</h4>
        <p class="text-gray-500">Images shared in this conversation will appear here</p>
      </div>
      
      <!-- Filtered Results -->
      <div v-else-if="filteredImages.length === 0" class="text-center py-8">
        <svg class="w-12 h-12 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
        </svg>
        <h4 class="text-lg font-medium text-gray-900 mb-2">No images found</h4>
        <p class="text-gray-500">Try adjusting your search or filters</p>
        <button
          @click="clearFilters"
          class="mt-3 text-blue-600 hover:text-blue-700 text-sm"
        >
          Clear filters
        </button>
      </div>
      
      <!-- Grid View -->
      <div 
        v-else-if="viewMode === 'grid'"
        class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3"
      >
        <div
          v-for="(image, index) in filteredImages"
          :key="image.id"
          class="group relative aspect-square bg-gray-100 rounded-lg overflow-hidden cursor-pointer hover:shadow-md transition-shadow duration-200"
          @click="openImage(filteredImages.indexOf(image))"
        >
          <img
            :src="image.preview_url || image.url"
            :alt="image.name"
            class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
            @load="onImageLoad"
            @error="onImageError"
          />
          
          <!-- Hover Overlay -->
          <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all duration-200 flex items-center justify-center">
            <svg class="w-8 h-8 text-white opacity-0 group-hover:opacity-100 transition-opacity duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
            </svg>
          </div>
          
          <!-- Image Info -->
          <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            <p class="text-white text-xs truncate">{{ image.name }}</p>
            <p class="text-gray-300 text-xs">{{ formatFileSize(image.size) }}</p>
          </div>
        </div>
      </div>
      
      <!-- List View -->
      <div v-else class="space-y-2">
        <div
          v-for="image in filteredImages"
          :key="image.id"
          class="flex items-center space-x-3 p-3 bg-gray-50 hover:bg-gray-100 rounded-lg cursor-pointer transition-colors duration-200"
          @click="openImage(filteredImages.indexOf(image))"
        >
          <!-- Thumbnail -->
          <img
            :src="image.preview_url || image.url"
            :alt="image.name"
            class="w-12 h-12 object-cover rounded-lg flex-shrink-0"
            @error="onImageError"
          />
          
          <!-- Info -->
          <div class="flex-1 min-w-0">
            <h4 class="font-medium text-gray-900 truncate">{{ image.name }}</h4>
            <div class="flex items-center space-x-2 text-sm text-gray-500">
              <span>{{ formatFileSize(image.size) }}</span>
              <span v-if="image.width && image.height">
                • {{ image.width }} × {{ image.height }}
              </span>
              <span>• {{ formatDate(image.uploaded_at) }}</span>
            </div>
          </div>
          
          <!-- Actions -->
          <div class="flex items-center space-x-2">
            <button
              @click.stop="downloadImage(image)"
              class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded-lg transition-colors"
              title="Download"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Lightbox -->
    <ImageDisplay
      v-if="showLightbox && currentImages.length > 0"
      :images="currentImages"
      @close="closeLightbox"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { ImageAttachment, ConversationMessage } from '@/types'
import ImageDisplay from './ImageDisplay.vue'

interface Props {
  messages: ConversationMessage[]
}

interface Emits {
  (e: 'close'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// State
const viewMode = ref<'grid' | 'list'>('grid')
const searchQuery = ref('')
const dateFilter = ref('all')
const typeFilter = ref('all')
const sortOrder = ref('newest')
const showLightbox = ref(false)
const currentImages = ref<ImageAttachment[]>([])

// Computed
const allImages = computed(() => {
  const images: ImageAttachment[] = []
  
  props.messages.forEach(message => {
    if (message.attachments && message.attachments.length > 0) {
      images.push(...message.attachments)
    }
  })
  
  return images
})

const filteredImages = computed(() => {
  let filtered = [...allImages.value]
  
  // Search filter
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(image =>
      image.name.toLowerCase().includes(query)
    )
  }
  
  // Date filter
  if (dateFilter.value !== 'all') {
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    
    filtered = filtered.filter(image => {
      const uploadDate = new Date(image.uploaded_at)
      
      switch (dateFilter.value) {
        case 'today':
          return uploadDate >= today
        case 'week':
          const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)
          return uploadDate >= weekAgo
        case 'month':
          const monthAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000)
          return uploadDate >= monthAgo
        default:
          return true
      }
    })
  }
  
  // Type filter
  if (typeFilter.value !== 'all') {
    filtered = filtered.filter(image => image.type === typeFilter.value)
  }
  
  // Sort
  filtered.sort((a, b) => {
    switch (sortOrder.value) {
      case 'oldest':
        return new Date(a.uploaded_at).getTime() - new Date(b.uploaded_at).getTime()
      case 'largest':
        return b.size - a.size
      case 'smallest':
        return a.size - b.size
      case 'name':
        return a.name.localeCompare(b.name)
      case 'newest':
      default:
        return new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime()
    }
  })
  
  return filtered
})

// Methods
const clearFilters = () => {
  searchQuery.value = ''
  dateFilter.value = 'all'
  typeFilter.value = 'all'
  sortOrder.value = 'newest'
}

const openImage = (index: number) => {
  currentImages.value = filteredImages.value
  showLightbox.value = true
  
  // You might want to set a current index here for the lightbox
  // This depends on how your ImageDisplay component works
}

const closeLightbox = () => {
  showLightbox.value = false
  currentImages.value = []
}

const downloadImage = async (image: ImageAttachment) => {
  try {
    const response = await fetch(image.url || '')
    const blob = await response.blob()
    
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = image.name
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  } catch (error) {
    console.error('Failed to download image:', error)
  }
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) {
    return date.toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    })
  } else if (diffDays === 1) {
    return 'Yesterday'
  } else if (diffDays < 7) {
    return `${diffDays} days ago`
  } else {
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    })
  }
}

const onImageLoad = (event: Event) => {
  // Handle successful image load if needed
}

const onImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  // You could set a fallback image here
  img.style.opacity = '0.5'
  console.error('Failed to load image:', img.src)
}
</script>

<style scoped>
.gallery-content {
  max-height: 70vh;
  overflow-y: auto;
}

/* Custom scrollbar */
.gallery-content::-webkit-scrollbar {
  width: 6px;
}

.gallery-content::-webkit-scrollbar-track {
  background: #f1f5f9;
}

.gallery-content::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.gallery-content::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* Mobile responsive */
@media (max-width: 640px) {
  .grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
  }
}

@media (min-width: 641px) and (max-width: 768px) {
  .sm\:grid-cols-3 {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (min-width: 769px) and (max-width: 1024px) {
  .md\:grid-cols-4 {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (min-width: 1025px) {
  .lg\:grid-cols-5 {
    grid-template-columns: repeat(5, 1fr);
  }
}
</style>