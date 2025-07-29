<template>
  <div
    @dragenter="handleDragEnter"
    @dragleave="handleDragLeave"
    @dragover="handleDragOver"
    @drop="handleDrop"
    :class="[
      'relative rounded-lg border-2 border-dashed p-6 text-center',
      isDragging
        ? 'border-primary-500 bg-primary-50'
        : 'border-gray-300 bg-white hover:border-gray-400'
    ]"
  >
    <input
      ref="inputRef"
      type="file"
      :multiple="multiple"
      :accept="acceptString"
      class="sr-only"
      @change="handleFileInput"
    />

    <CloudArrowUpIcon class="mx-auto h-12 w-12 text-gray-400" />
    
    <div class="mt-4">
      <button
        type="button"
        @click="openFileDialog"
        class="relative cursor-pointer rounded-md font-medium text-primary-600 hover:text-primary-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-primary-500 focus-within:ring-offset-2"
      >
        <span>Upload files</span>
      </button>
      <p class="pl-1 text-gray-600">or drag and drop</p>
    </div>
    
    <p class="text-xs text-gray-500 mt-2">
      {{ acceptedTypesText }} up to {{ maxSize }}MB each
    </p>

    <!-- File list -->
    <div v-if="files.length > 0" class="mt-6">
      <ul role="list" class="divide-y divide-gray-200 rounded-md border border-gray-200">
        <li
          v-for="(file, index) in files"
          :key="`${file.file.name}-${index}`"
          class="flex items-center justify-between py-3 pl-3 pr-4 text-sm"
        >
          <div class="flex w-0 flex-1 items-center">
            <PaperClipIcon class="h-5 w-5 flex-shrink-0 text-gray-400" aria-hidden="true" />
            <span class="ml-2 w-0 flex-1 truncate">{{ file.file.name }}</span>
            <span class="ml-2 flex-shrink-0 text-gray-400">
              {{ formatFileSize(file.file.size) }}
            </span>
          </div>
          
          <div class="ml-4 flex items-center space-x-2">
            <!-- Progress bar -->
            <div v-if="file.status === 'uploading'" class="w-20">
              <div class="overflow-hidden rounded-full bg-gray-200">
                <div
                  class="h-2 rounded-full bg-primary-600 transition-all duration-300"
                  :style="{ width: `${file.progress}%` }"
                />
              </div>
            </div>
            
            <!-- Status icons -->
            <CheckCircleIcon
              v-if="file.status === 'completed'"
              class="h-5 w-5 text-green-500"
              aria-hidden="true"
            />
            <ExclamationCircleIcon
              v-if="file.status === 'error'"
              class="h-5 w-5 text-red-500"
              aria-hidden="true"
            />
            
            <!-- Remove button -->
            <button
              type="button"
              @click="removeFile(index)"
              :disabled="file.status === 'uploading'"
              class="text-gray-400 hover:text-gray-500 disabled:opacity-50"
            >
              <XMarkIcon class="h-5 w-5" aria-hidden="true" />
            </button>
          </div>
        </li>
      </ul>
      
      <!-- Error messages -->
      <div v-for="(file, index) in files.filter(f => f.error)" :key="`error-${index}`" class="mt-2">
        <p class="text-sm text-red-600">
          {{ file.file.name }}: {{ file.error }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useFileUpload } from '@/composables/useFileUpload'
import { formatFileSize } from '@/utils/formatters'
import {
  CloudArrowUpIcon,
  PaperClipIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  XMarkIcon,
} from '@heroicons/vue/24/outline'

export interface FileUploadZoneProps {
  accept?: string[]
  maxSize?: number
  maxFiles?: number
  multiple?: boolean
  onUpload?: (file: File) => Promise<void>
}

const props = withDefaults(defineProps<FileUploadZoneProps>(), {
  accept: () => [],
  maxSize: 10,
  maxFiles: 5,
  multiple: true,
})

const emit = defineEmits<{
  'files-selected': [files: File[]]
  'upload-complete': [files: File[]]
}>()

const {
  files,
  isDragging,
  inputRef,
  addFiles,
  removeFile,
  openFileDialog,
  handleDragEnter,
  handleDragLeave,
  handleDragOver,
  handleDrop,
  handleFileInput,
  completedFiles,
} = useFileUpload({
  accept: props.accept,
  maxSize: props.maxSize,
  maxFiles: props.maxFiles,
  onUpload: props.onUpload,
})

// Watch for completed files
completedFiles.value && emit('upload-complete', completedFiles.value.map(f => f.file))

const acceptString = computed(() => props.accept.join(','))

const acceptedTypesText = computed(() => {
  if (props.accept.length === 0) return 'Any file type'
  
  const types = props.accept.map(type => {
    if (type.startsWith('.')) return type.toUpperCase().slice(1)
    if (type.includes('/')) {
      const [category, subtype] = type.split('/')
      if (subtype === '*') return category.toUpperCase()
      return subtype.toUpperCase()
    }
    return type.toUpperCase()
  })
  
  return types.join(', ')
})
</script>