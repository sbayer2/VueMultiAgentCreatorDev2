<template>
  <div class="image-display">
    <!-- Single Image Display -->
    <div
      v-if="images.length === 1"
      class="single-image-container"
      @click="openLightbox(0)"
    >
      <img
        :src="getImageUrl(images[0])"
        :alt="images[0].name"
        class="single-image cursor-pointer rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200"
        :style="singleImageStyle"
        @load="onImageLoad($event, images[0])"
        @error="onImageError($event, images[0])"
      />
      
      <!-- Image Info Overlay -->
      <div class="absolute bottom-2 right-2 bg-black bg-opacity-60 text-white text-xs px-2 py-1 rounded opacity-0 hover:opacity-100 transition-opacity duration-200">
        {{ images[0].name }}
      </div>
    </div>
    
    <!-- Multiple Images Grid -->
    <div v-else-if="images.length > 1" class="multi-image-grid">
      <div
        v-for="(image, index) in displayImages"
        :key="image.id"
        :class="[
          'image-item cursor-pointer rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow duration-200',
          getImageItemClass(index)
        ]"
        @click="openLightbox(index)"
      >
        <img
          :src="getImageUrl(image)"
          :alt="image.name"
          class="w-full h-full object-cover"
          @load="onImageLoad($event, image)"
          @error="onImageError($event, image)"
        />
        
        <!-- More Images Overlay -->
        <div
          v-if="index === maxDisplayImages - 1 && images.length > maxDisplayImages"
          class="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center text-white font-medium text-lg"
        >
          +{{ images.length - maxDisplayImages }}
        </div>
      </div>
    </div>
    
    <!-- Image Loading States -->
    <div
      v-if="loadingStates.some(state => state.loading)"
      class="flex items-center space-x-2 mt-2 text-sm text-gray-500"
    >
      <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle
          class="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          stroke-width="4"
        />
        <path
          class="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
      <span>Loading images...</span>
    </div>
    
    <!-- Lightbox Modal -->
    <Teleport to="body">
      <div
        v-if="showLightbox"
        class="fixed inset-0 z-50 bg-black bg-opacity-90 flex items-center justify-center"
        @click="closeLightbox"
        @keydown.esc="closeLightbox"
        tabindex="0"
      >
        <!-- Close Button -->
        <button
          @click="closeLightbox"
          class="absolute top-4 right-4 z-10 p-2 text-white hover:text-gray-300 bg-black bg-opacity-50 rounded-full"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
        
        <!-- Image Navigation -->
        <div
          v-if="images.length > 1"
          class="absolute inset-y-0 left-4 flex items-center"
        >
          <button
            @click.stop="previousImage"
            :disabled="currentImageIndex === 0"
            class="p-2 text-white hover:text-gray-300 bg-black bg-opacity-50 rounded-full disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
            </svg>
          </button>
        </div>
        
        <div
          v-if="images.length > 1"
          class="absolute inset-y-0 right-4 flex items-center"
        >
          <button
            @click.stop="nextImage"
            :disabled="currentImageIndex === images.length - 1"
            class="p-2 text-white hover:text-gray-300 bg-black bg-opacity-50 rounded-full disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </button>
        </div>
        
        <!-- Main Image -->
        <div 
          class="max-w-screen-lg max-h-screen-90 mx-4"
          @click.stop
        >
          <img
            :src="currentImage ? getImageUrl(currentImage) : ''"
            :alt="currentImage?.name"
            class="max-w-full max-h-full object-contain"
          />
          
          <!-- Image Info -->
          <div class="mt-4 text-center text-white">
            <h3 class="text-lg font-medium">{{ currentImage?.name }}</h3>
            <p class="text-sm text-gray-300">
              {{ formatFileSize(currentImage?.size || 0) }}
              <span v-if="currentImage?.width && currentImage?.height">
                • {{ currentImage.width }} × {{ currentImage.height }}
              </span>
              <span v-if="images.length > 1">
                • {{ currentImageIndex + 1 }} of {{ images.length }}
              </span>
            </p>
          </div>
        </div>
        
        <!-- Image Thumbnails -->
        <div
          v-if="images.length > 1"
          class="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex space-x-2 bg-black bg-opacity-50 rounded-lg p-2"
        >
          <button
            v-for="(image, index) in images"
            :key="image.id"
            @click.stop="setCurrentImage(index)"
            :class="[
              'w-12 h-12 rounded overflow-hidden border-2 transition-all duration-200',
              index === currentImageIndex
                ? 'border-white'
                : 'border-transparent opacity-70 hover:opacity-100'
            ]"
          >
            <img
              :src="getImageUrl(image)"
              :alt="image.name"
              class="w-full h-full object-cover"
            />
          </button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { ImageAttachment } from '@/types'

interface Props {
  images: ImageAttachment[]
  maxWidth?: number
  maxHeight?: number
  maxDisplayImages?: number
  layout?: 'single' | 'grid' | 'auto'
}

const props = withDefaults(defineProps<Props>(), {
  maxWidth: 400,
  maxHeight: 300,
  maxDisplayImages: 4,
  layout: 'auto'
})

// Reactive state
const showLightbox = ref(false)
const currentImageIndex = ref(0)
const loadingStates = ref<Array<{ id: string; loading: boolean }>>([])

// Computed properties
const displayImages = computed(() => {
  return props.images.slice(0, props.maxDisplayImages)
})

const currentImage = computed(() => {
  return props.images[currentImageIndex.value]
})

const singleImageStyle = computed(() => {
  return {
    maxWidth: `${props.maxWidth}px`,
    maxHeight: `${props.maxHeight}px`
  }
})

// Methods
const getImageUrl = (image: ImageAttachment) => {
  // Use existing URL if available, otherwise build URL from file_id
  if (image.url || image.preview_url) {
    return image.preview_url || image.url
  }
  // Build absolute URL to backend for MMACTEMP pattern
  // VITE_API_URL includes /api, so we append /files/openai/{file_id}
  const apiBaseUrl = import.meta.env.VITE_API_URL || '/api'
  return `${apiBaseUrl}/files/openai/${image.file_id}`
}

const onImageLoad = (event: Event, image: ImageAttachment) => {
  const target = event.target as HTMLImageElement
  
  // Update loading state
  const loadingIndex = loadingStates.value.findIndex(state => state.id === image.id)
  if (loadingIndex !== -1) {
    loadingStates.value[loadingIndex].loading = false
  }
  
  // Store natural dimensions if not available
  if (!image.width || !image.height) {
    image.width = target.naturalWidth
    image.height = target.naturalHeight
  }
}

const onImageError = (event: Event, image: ImageAttachment) => {
  console.error('Failed to load image:', image.name, image.url)
  
  // Update loading state
  const loadingIndex = loadingStates.value.findIndex(state => state.id === image.id)
  if (loadingIndex !== -1) {
    loadingStates.value[loadingIndex].loading = false
  }
  
  // You could add a fallback image or error state here
  const target = event.target as HTMLImageElement
  target.style.display = 'none'
}

const getImageItemClass = (index: number) => {
  const count = Math.min(props.images.length, props.maxDisplayImages)
  
  if (count === 2) {
    return 'aspect-square'
  } else if (count === 3) {
    return index === 0 ? 'col-span-2 aspect-video' : 'aspect-square'
  } else if (count >= 4) {
    return 'aspect-square'
  }
  
  return 'aspect-square'
}

const openLightbox = (index: number) => {
  currentImageIndex.value = index
  showLightbox.value = true
  document.body.style.overflow = 'hidden'
}

const closeLightbox = () => {
  showLightbox.value = false
  document.body.style.overflow = ''
}

const previousImage = () => {
  if (currentImageIndex.value > 0) {
    currentImageIndex.value--
  }
}

const nextImage = () => {
  if (currentImageIndex.value < props.images.length - 1) {
    currentImageIndex.value++
  }
}

const setCurrentImage = (index: number) => {
  currentImageIndex.value = index
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// Keyboard navigation
const handleKeydown = (event: KeyboardEvent) => {
  if (!showLightbox.value) return
  
  switch (event.key) {
    case 'ArrowLeft':
      event.preventDefault()
      previousImage()
      break
    case 'ArrowRight':
      event.preventDefault()
      nextImage()
      break
    case 'Escape':
      event.preventDefault()
      closeLightbox()
      break
  }
}

// Lifecycle
onMounted(() => {
  // Initialize loading states
  loadingStates.value = props.images.map(image => ({
    id: image.id,
    loading: true
  }))
  
  // Add keyboard event listener
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  document.body.style.overflow = ''
})
</script>

<style scoped>
.image-display {
  position: relative;
}

.single-image-container {
  position: relative;
  display: inline-block;
}

.single-image {
  display: block;
  height: auto;
}

.multi-image-grid {
  display: grid;
  gap: 0.25rem;
  grid-template-columns: repeat(2, 1fr);
}

.multi-image-grid:has(.col-span-2) {
  grid-template-columns: repeat(2, 1fr);
}

.image-item {
  position: relative;
  overflow: hidden;
}

.col-span-2 {
  grid-column: span 2;
}

.aspect-square {
  aspect-ratio: 1 / 1;
}

.aspect-video {
  aspect-ratio: 16 / 9;
}

.max-h-screen-90 {
  max-height: 90vh;
}

/* Mobile responsive adjustments */
@media (max-width: 640px) {
  .multi-image-grid {
    gap: 0.125rem;
  }
  
  .single-image {
    max-width: 100%;
  }
}

/* Touch targets for mobile */
@media (hover: none) and (pointer: coarse) {
  .image-item {
    min-height: 44px;
    min-width: 44px;
  }
}

/* Animation for lightbox */
.lightbox-enter-active,
.lightbox-leave-active {
  transition: opacity 0.3s ease;
}

.lightbox-enter-from,
.lightbox-leave-to {
  opacity: 0;
}
</style>