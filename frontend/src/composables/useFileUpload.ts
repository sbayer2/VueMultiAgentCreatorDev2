import { ref, computed } from 'vue'
import type { FileUploadProgress } from '@/types'

export interface UseFileUploadOptions {
  accept?: string[]
  maxSize?: number // in MB
  maxFiles?: number
  onUpload?: (file: File) => Promise<void>
}

export function useFileUpload(options: UseFileUploadOptions = {}) {
  const {
    accept = [],
    maxSize = 10,
    maxFiles = 5,
    onUpload,
  } = options

  // State
  const files = ref<FileUploadProgress[]>([])
  const isDragging = ref(false)
  const inputRef = ref<HTMLInputElement | null>(null)

  // Computed
  const totalProgress = computed(() => {
    if (files.value.length === 0) return 0
    const sum = files.value.reduce((acc, file) => acc + file.progress, 0)
    return Math.round(sum / files.value.length)
  })

  const isUploading = computed(() =>
    files.value.some(file => file.status === 'uploading')
  )

  const hasErrors = computed(() =>
    files.value.some(file => file.status === 'error')
  )

  const completedFiles = computed(() =>
    files.value.filter(file => file.status === 'completed')
  )

  // Methods
  const validateFile = (file: File): string | null => {
    // Check file size
    const maxSizeInBytes = maxSize * 1024 * 1024
    if (file.size > maxSizeInBytes) {
      return `File size exceeds ${maxSize}MB limit`
    }

    // Check file type
    if (accept.length > 0) {
      const isValidType = accept.some(type => {
        if (type.startsWith('.')) {
          return file.name.toLowerCase().endsWith(type.toLowerCase())
        }
        if (type.endsWith('/*')) {
          const category = type.split('/')[0]
          return file.type.startsWith(category)
        }
        return file.type === type
      })

      if (!isValidType) {
        return `File type not allowed. Accepted types: ${accept.join(', ')}`
      }
    }

    return null
  }

  const addFiles = async (newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles)

    // Check max files limit
    if (files.value.length + fileArray.length > maxFiles) {
      throw new Error(`Maximum ${maxFiles} files allowed`)
    }

    // Validate and add files
    for (const file of fileArray) {
      const error = validateFile(file)
      
      const fileProgress: FileUploadProgress = {
        file,
        progress: 0,
        status: error ? 'error' : 'pending',
        error,
      }

      files.value.push(fileProgress)

      if (!error && onUpload) {
        uploadFile(fileProgress)
      }
    }
  }

  const uploadFile = async (fileProgress: FileUploadProgress) => {
    try {
      fileProgress.status = 'uploading'
      
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        if (fileProgress.progress < 90) {
          fileProgress.progress += 10
        }
      }, 200)

      await onUpload!(fileProgress.file)

      clearInterval(progressInterval)
      fileProgress.progress = 100
      fileProgress.status = 'completed'
    } catch (error: any) {
      fileProgress.status = 'error'
      fileProgress.error = error.message || 'Upload failed'
    }
  }

  const removeFile = (index: number) => {
    files.value.splice(index, 1)
  }

  const clearFiles = () => {
    files.value = []
  }

  const openFileDialog = () => {
    inputRef.value?.click()
  }

  // Drag and drop handlers
  const handleDragEnter = (e: DragEvent) => {
    e.preventDefault()
    isDragging.value = true
  }

  const handleDragLeave = (e: DragEvent) => {
    e.preventDefault()
    isDragging.value = false
  }

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault()
  }

  const handleDrop = async (e: DragEvent) => {
    e.preventDefault()
    isDragging.value = false

    const droppedFiles = e.dataTransfer?.files
    if (droppedFiles) {
      try {
        await addFiles(droppedFiles)
      } catch (error: any) {
        console.error('Drop error:', error)
      }
    }
  }

  const handleFileInput = async (e: Event) => {
    const input = e.target as HTMLInputElement
    const selectedFiles = input.files

    if (selectedFiles) {
      try {
        await addFiles(selectedFiles)
      } catch (error: any) {
        console.error('File input error:', error)
      }
    }

    // Reset input
    input.value = ''
  }

  return {
    // State
    files,
    isDragging,
    inputRef,
    
    // Computed
    totalProgress,
    isUploading,
    hasErrors,
    completedFiles,
    
    // Methods
    addFiles,
    removeFile,
    clearFiles,
    openFileDialog,
    
    // Drag and drop handlers
    handleDragEnter,
    handleDragLeave,
    handleDragOver,
    handleDrop,
    handleFileInput,
  }
}