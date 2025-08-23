<template>
  <div class="file-upload">
    <div
      @drop="handleDrop"
      @dragover="handleDragOver"
      @dragenter.prevent
      @dragleave="handleDragLeave"
      :class="[
        'border-2 border-dashed rounded-lg p-6 text-center transition-colors',
        isDragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-gray-50',
        isUploading ? 'opacity-50' : ''
      ]"
    >
      <div class="flex flex-col items-center">
        <svg class="w-12 h-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
        </svg>
        
        <p class="text-lg font-medium text-gray-900 mb-2">
          Drop files here or click to upload
        </p>
        
        <p class="text-sm text-gray-600 mb-4">
          Supports images (JPG, PNG, GIF, WebP) and documents
        </p>
        
        <button
          type="button"
          @click="triggerFileInput"
          :disabled="isUploading"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ isUploading ? 'Uploading...' : 'Select Files' }}
        </button>
      </div>
      
      <input
        ref="fileInput"
        type="file"
        multiple
        accept=".jpg,.jpeg,.png,.gif,.webp,.pdf,.txt,.doc,.docx,.csv,.json"
        @change="handleFileSelect"
        class="hidden"
      />
    </div>
    
    <!-- File List -->
    <div v-if="uploadedFiles.length > 0" class="mt-4">
      <h4 class="text-sm font-medium text-gray-900 mb-2">Uploaded Files ({{ uploadedFiles.length }})</h4>
      <div class="space-y-2">
        <div
          v-for="file in uploadedFiles"
          :key="file.file_id"
          class="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg"
        >
          <div class="flex items-center space-x-3">
            <div class="flex-shrink-0">
              <svg v-if="isImageFile(file.filename)" class="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
              </svg>
              <svg v-else class="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
              </svg>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-900">{{ file.filename }}</p>
              <p class="text-xs text-gray-500">{{ formatFileSize(file.size) }} • {{ file.purpose }}</p>
            </div>
          </div>
          
          <button
            @click="removeFile(file)"
            class="flex-shrink-0 p-1 text-red-500 hover:text-red-700 transition-colors"
            title="Remove file"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
      </div>
    </div>
    
    <!-- Upload Progress -->
    <div v-if="uploadProgress.length > 0" class="mt-4">
      <h4 class="text-sm font-medium text-gray-900 mb-2">Uploading...</h4>
      <div class="space-y-2">
        <div
          v-for="progress in uploadProgress"
          :key="progress.id"
          class="p-3 bg-blue-50 border border-blue-200 rounded-lg"
        >
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-medium text-blue-900">{{ progress.filename }}</span>
            <span class="text-xs text-blue-600">{{ progress.progress }}%</span>
          </div>
          <div class="w-full bg-blue-200 rounded-full h-2">
            <div
              class="bg-blue-600 h-2 rounded-full transition-all duration-300"
              :style="{ width: `${progress.progress}%` }"
            ></div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Error Messages -->
    <div v-if="errorMessages.length > 0" class="mt-4">
      <div
        v-for="error in errorMessages"
        :key="error.id"
        class="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800"
      >
        {{ error.message }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { apiClient } from '@/utils/api'

interface UploadedFile {
  file_id: string
  filename: string
  size: number
  purpose: string
}

interface UploadProgress {
  id: string
  filename: string
  progress: number
}

interface ErrorMessage {
  id: string
  message: string
}

// Props
const props = defineProps<{
  modelValue: string[] // Array of file IDs
}>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [fileIds: string[]]
}>()

// State
const isDragOver = ref(false)
const isUploading = ref(false)
const fileInput = ref<HTMLInputElement>()
const uploadedFiles = ref<UploadedFile[]>([])
const uploadProgress = ref<UploadProgress[]>([])
const errorMessages = ref<ErrorMessage[]>([])

// Computed
const fileIds = computed(() => uploadedFiles.value.map(f => f.file_id))

// Methods
const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = false
  
  const files = event.dataTransfer?.files
  if (files) {
    handleFiles(Array.from(files))
  }
}

const handleDragLeave = () => {
  isDragOver.value = false
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files) {
    handleFiles(Array.from(target.files))
  }
}

const handleFiles = async (files: File[]) => {
  if (isUploading.value) return
  
  // Clear previous errors
  errorMessages.value = []
  
  // Validate files
  const validFiles = files.filter(file => {
    if (file.size > 25 * 1024 * 1024) { // 25MB limit
      addError(`File "${file.name}" is too large (max 25MB)`)
      return false
    }
    return true
  })
  
  if (validFiles.length === 0) return
  
  isUploading.value = true
  
  // Upload files
  for (const file of validFiles) {
    await uploadFile(file)
  }
  
  isUploading.value = false
  
  // Emit updated file IDs
  emit('update:modelValue', fileIds.value)
}

const uploadFile = async (file: File) => {
  const progressId = Math.random().toString(36).substr(2, 9)
  
  // Add to progress tracking
  uploadProgress.value.push({
    id: progressId,
    filename: file.name,
    progress: 0
  })
  
  try {
    // For assistant creation, all files (including images) should be 'assistants' 
    // so they can be attached to the assistant's tool_resources
    const purpose = 'assistants'
    
    // Create form data
    const formData = new FormData()
    formData.append('file', file)
    formData.append('purpose', purpose)
    
    // Use the new unified assistant upload endpoint
    const endpoint = '/files/upload-for-assistant'
    
    // Simulate progress (since we can't track real upload progress with fetch)
    const progressInterval = setInterval(() => {
      const progressItem = uploadProgress.value.find(p => p.id === progressId)
      if (progressItem && progressItem.progress < 90) {
        progressItem.progress += 10
      }
    }, 200)
    
    // Upload file using apiClient
    const response = await apiClient.post(endpoint, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    clearInterval(progressInterval)
    
    if (!response.success) {
      throw new Error(response.error?.message || 'Upload failed')
    }
    
    const result = response.data
    
    // Update progress to 100%
    const progressItem = uploadProgress.value.find(p => p.id === progressId)
    if (progressItem) {
      progressItem.progress = 100
    }
    
    // Add to uploaded files
    uploadedFiles.value.push({
      file_id: result.file_id,
      filename: result.filename || result.name,
      size: result.size,
      purpose: result.purpose || purpose
    })
    
    // Remove from progress after a delay
    setTimeout(() => {
      uploadProgress.value = uploadProgress.value.filter(p => p.id !== progressId)
    }, 1000)
    
  } catch (error: any) {
    // Remove from progress
    uploadProgress.value = uploadProgress.value.filter(p => p.id !== progressId)
    
    // Add error message
    addError(`Failed to upload "${file.name}": ${error.message}`)
  }
}

const removeFile = async (file: UploadedFile) => {
  try {
    // Delete from backend
    await apiClient.delete(`/files/${file.file_id}`)
    
    // Remove from local state
    uploadedFiles.value = uploadedFiles.value.filter(f => f.file_id !== file.file_id)
    
    // Emit updated file IDs
    emit('update:modelValue', fileIds.value)
    
  } catch (error: any) {
    addError(`Failed to delete "${file.filename}": ${error.message}`)
  }
}

const isImageFile = (filename: string): boolean => {
  const extension = filename.split('.').pop()?.toLowerCase()
  return ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(extension || '')
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const addError = (message: string) => {
  const errorId = Math.random().toString(36).substr(2, 9)
  errorMessages.value.push({ id: errorId, message })
  
  // Remove error after 5 seconds
  setTimeout(() => {
    errorMessages.value = errorMessages.value.filter(e => e.id !== errorId)
  }, 5000)
}

// Handle drag events on the container
const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = true
}

// Watch for changes in modelValue to sync with parent
watch(() => props.modelValue, (newFileIds) => {
  // If parent updates file IDs, we might need to sync our local state
  // For now, we'll trust that our emitted changes are the source of truth
}, { immediate: true })
</script>

<style scoped>
.file-upload {
  @apply w-full;
}
</style>