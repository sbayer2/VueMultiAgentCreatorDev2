<template>
  <div class="image-upload-container">
    <!-- Upload Drop Zone -->
    <div
      ref="dropZone"
      @drop.prevent="onDrop"
      @dragover.prevent="onDragOver"
      @dragleave.prevent="onDragLeave"
      @dragenter.prevent
      @click="triggerFileSelect"
      :class="[
        'upload-drop-zone transition-all duration-200 ease-in-out',
        isDragging 
          ? 'border-blue-400 bg-blue-50' 
          : 'border-gray-300 hover:border-gray-400',
        'border-2 border-dashed rounded-lg p-4 text-center cursor-pointer'
      ]"
    >
      <!-- Upload Icon and Text -->
      <div class="flex flex-col items-center space-y-2">
        <svg 
          class="w-8 h-8 text-gray-400" 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path 
            stroke-linecap="round" 
            stroke-linejoin="round" 
            stroke-width="2" 
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>
        
        <div class="text-sm text-gray-600">
          <span class="font-medium text-blue-600 hover:text-blue-500">
            Click to upload images
          </span>
          or drag and drop
        </div>
        
        <p class="text-xs text-gray-500">
          PNG, JPG, GIF up to 10MB
        </p>
      </div>
      
      <!-- Hidden File Input -->
      <input
        ref="fileInput"
        type="file"
        multiple
        accept="image/*"
        @change="onFileSelect"
        class="hidden"
      />
    </div>
    
    <!-- Upload Progress and Previews -->
    <div v-if="uploadQueue.length > 0" class="mt-4 space-y-3">
      <div
        v-for="upload in uploadQueue"
        :key="upload.id"
        class="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg"
      >
        <!-- Image Preview -->
        <div class="flex-shrink-0">
          <img
            v-if="upload.preview"
            :src="upload.preview"
            alt="Preview"
            class="w-12 h-12 object-cover rounded-lg"
          />
          <div 
            v-else
            class="w-12 h-12 bg-gray-200 rounded-lg flex items-center justify-center"
          >
            <svg class="w-6 h-6 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
              <path 
                fill-rule="evenodd" 
                d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" 
                clip-rule="evenodd"
              />
            </svg>
          </div>
        </div>
        
        <!-- Upload Info -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between">
            <p class="text-sm font-medium text-gray-900 truncate">
              {{ upload.file.name }}
            </p>
            <button
              @click="removeFromQueue(upload.id)"
              :disabled="upload.status === 'uploading'"
              class="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50"
            >
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path 
                  fill-rule="evenodd" 
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" 
                  clip-rule="evenodd"
                />
              </svg>
            </button>
          </div>
          
          <p class="text-xs text-gray-500">
            {{ formatFileSize(upload.file.size) }}
          </p>
          
          <!-- Progress Bar -->
          <div v-if="upload.status === 'uploading'" class="mt-2">
            <div class="w-full bg-gray-200 rounded-full h-1.5">
              <div 
                class="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                :style="{ width: `${upload.progress}%` }"
              ></div>
            </div>
            <p class="text-xs text-blue-600 mt-1">
              Uploading... {{ upload.progress }}%
            </p>
          </div>
          
          <!-- Status Messages -->
          <div v-else-if="upload.status === 'processing'" class="mt-1">
            <p class="text-xs text-yellow-600">Processing image...</p>
          </div>
          
          <div v-else-if="upload.status === 'completed'" class="mt-1">
            <p class="text-xs text-green-600">✓ Upload complete</p>
          </div>
          
          <div v-else-if="upload.status === 'error'" class="mt-1">
            <p class="text-xs text-red-600">{{ upload.error || 'Upload failed' }}</p>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Uploaded Images Preview -->
    <div v-if="uploadedImages.length > 0" class="mt-4">
      <h4 class="text-sm font-medium text-gray-900 mb-2">
        Attached Images ({{ uploadedImages.length }})
      </h4>
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
        <div
          v-for="image in uploadedImages"
          :key="image.id"
          class="relative group aspect-square"
        >
          <img
            :src="image.preview_url || image.url"
            :alt="image.name"
            class="w-full h-full object-cover rounded-lg"
          />
          
          <!-- Remove Button -->
          <button
            @click="removeUploadedImage(image.id)"
            class="absolute top-1 right-1 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-200 hover:bg-red-600"
          >
            <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path 
                fill-rule="evenodd" 
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" 
                clip-rule="evenodd"
              />
            </svg>
          </button>
          
          <!-- Image Info on Hover -->
          <div class="absolute bottom-0 left-0 right-0 bg-black bg-opacity-75 text-white text-xs p-2 rounded-b-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            <p class="truncate">{{ image.name }}</p>
            <p>{{ formatFileSize(image.size) }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import type { ImageAttachment, ImageUploadStatus } from '@/types'
import { apiClient } from '@/utils/api'

interface Props {
  maxFiles?: number
  maxFileSize?: number // in bytes
  acceptedTypes?: string[]
}

interface Emits {
  (e: 'upload-complete', images: ImageAttachment[]): void
  (e: 'upload-error', error: string): void
  (e: 'images-changed', images: ImageAttachment[]): void
}

const props = withDefaults(defineProps<Props>(), {
  maxFiles: 5,
  maxFileSize: 10 * 1024 * 1024, // 10MB
  acceptedTypes: () => ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
})

const emit = defineEmits<Emits>()

// Refs
const dropZone = ref<HTMLDivElement>()
const fileInput = ref<HTMLInputElement>()
const isDragging = ref(false)
const uploadQueue = ref<(ImageUploadStatus & { preview?: string })[]>([])
const uploadedImages = ref<ImageAttachment[]>([])

// Methods
const onDragOver = () => {
  isDragging.value = true
}

const onDragLeave = (e: DragEvent) => {
  if (!dropZone.value?.contains(e.relatedTarget as Node)) {
    isDragging.value = false
  }
}

const onDrop = (e: DragEvent) => {
  isDragging.value = false
  const files = Array.from(e.dataTransfer?.files || [])
  processFiles(files)
}

const onFileSelect = (e: Event) => {
  const files = Array.from((e.target as HTMLInputElement).files || [])
  processFiles(files)
}

const processFiles = async (files: File[]) => {
  // Validate file count
  const totalFiles = uploadedImages.value.length + files.length
  if (totalFiles > props.maxFiles) {
    emit('upload-error', `Maximum ${props.maxFiles} images allowed`)
    return
  }
  
  // Process each file
  for (const file of files) {
    // Validate file type
    if (!props.acceptedTypes.includes(file.type)) {
      emit('upload-error', `Unsupported file type: ${file.type}`)
      continue
    }
    
    // Validate file size
    if (file.size > props.maxFileSize) {
      emit('upload-error', `File too large: ${file.name} (max ${formatFileSize(props.maxFileSize)})`)
      continue
    }
    
    // Create upload status
    const uploadStatus: ImageUploadStatus & { preview?: string } = {
      id: generateId(),
      file,
      progress: 0,
      status: 'pending'
    }
    
    // Generate preview
    try {
      uploadStatus.preview = await createImagePreview(file)
    } catch (error) {
      console.warn('Failed to create preview for', file.name, error)
    }
    
    uploadQueue.value.push(uploadStatus)
    
    // Start upload
    uploadImage(uploadStatus)
  }
  
  // Clear file input
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const uploadImage = async (uploadStatus: ImageUploadStatus & { preview?: string }) => {
  uploadStatus.status = 'uploading'
  
  try {
    const formData = new FormData()
    formData.append('file', uploadStatus.file)
    formData.append('purpose', 'vision') // For OpenAI vision API
    
    const response = await apiClient.post('/api/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total) {
          uploadStatus.progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        }
      }
    })
    
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || 'Upload failed')
    }
    
    uploadStatus.status = 'processing'
    
    // Process the uploaded file
    const imageAttachment: ImageAttachment = {
      id: response.data.id,
      file_id: response.data.file_id,
      name: response.data.filename,
      size: response.data.size,
      type: response.data.content_type,
      url: response.data.url,
      preview_url: response.data.preview_url,
      width: response.data.width,
      height: response.data.height,
      uploaded_at: new Date().toISOString()
    }
    
    uploadStatus.status = 'completed'
    uploadStatus.result = imageAttachment
    
    // Add to uploaded images
    uploadedImages.value.push(imageAttachment)
    
    // Remove from queue after a short delay
    setTimeout(() => {
      const index = uploadQueue.value.findIndex(u => u.id === uploadStatus.id)
      if (index !== -1) {
        uploadQueue.value.splice(index, 1)
      }
    }, 2000)
    
    // Emit events
    emit('upload-complete', [imageAttachment])
    emit('images-changed', uploadedImages.value)
    
  } catch (error: any) {
    uploadStatus.status = 'error'
    uploadStatus.error = error.message || 'Upload failed'
    emit('upload-error', uploadStatus.error)
  }
}

const removeFromQueue = (uploadId: string) => {
  const index = uploadQueue.value.findIndex(u => u.id === uploadId)
  if (index !== -1) {
    uploadQueue.value.splice(index, 1)
  }
}

const removeUploadedImage = (imageId: string) => {
  const index = uploadedImages.value.findIndex(img => img.id === imageId)
  if (index !== -1) {
    uploadedImages.value.splice(index, 1)
    emit('images-changed', uploadedImages.value)
  }
}

const createImagePreview = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => resolve(e.target?.result as string)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const generateId = (): string => {
  return Date.now().toString(36) + Math.random().toString(36).substr(2)
}

// Public methods
const clearImages = () => {
  uploadedImages.value = []
  uploadQueue.value = []
  emit('images-changed', uploadedImages.value)
}

const getUploadedImages = (): ImageAttachment[] => {
  return [...uploadedImages.value]
}

// Click handler for drop zone
const triggerFileSelect = () => {
  fileInput.value?.click()
}

// Expose public methods
defineExpose({
  clearImages,
  getUploadedImages
})
</script>

<style scoped>
.upload-drop-zone {
  min-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-drop-zone:hover {
  background-color: #fafafa;
}

/* Responsive grid for image previews */
@media (max-width: 640px) {
  .grid-cols-2 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 641px) and (max-width: 768px) {
  .sm\:grid-cols-3 {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (min-width: 769px) {
  .md\:grid-cols-4 {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}
</style>