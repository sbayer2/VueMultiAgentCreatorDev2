import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient } from '@/utils/api'
import type { Assistant, CreateAssistantData, PaginatedResponse } from '@/types'

export const useAssistantsStore = defineStore('assistants', () => {
  // State
  const assistants = ref<Assistant[]>([])
  const currentAssistant = ref<Assistant | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const totalCount = ref(0)

  // Getters
  const assistantsList = computed(() => assistants.value)
  const assistantsCount = computed(() => assistants.value.length)
  const getAssistantById = computed(() => (id: string) => 
    assistants.value.find(a => a.id === id)
  )

  // Actions
  const fetchAssistants = async (page = 1, limit = 20) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiClient.get<PaginatedResponse<Assistant>>('/assistants', {
        params: { page, limit }
      })
      
      if (response.success && response.data) {
        assistants.value = response.data.items
        totalCount.value = response.data.total
        return { success: true, data: response.data }
      } else {
        error.value = response.error?.message || 'Failed to fetch assistants'
        return { success: false, error: error.value }
      }
    } catch (err) {
      error.value = 'An unexpected error occurred'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  const fetchAssistant = async (id: string) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiClient.get<Assistant>(`/assistants/${id}`)
      
      if (response.success && response.data) {
        currentAssistant.value = response.data
        
        // Update in list if exists
        const index = assistants.value.findIndex(a => a.id === id)
        if (index !== -1) {
          assistants.value[index] = response.data
        }
        
        return { success: true, data: response.data }
      } else {
        error.value = response.error?.message || 'Failed to fetch assistant'
        return { success: false, error: error.value }
      }
    } catch (err) {
      error.value = 'An unexpected error occurred'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  const createAssistant = async (data: CreateAssistantData) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiClient.post<Assistant>('/assistants', data)
      
      if (response.success && response.data) {
        assistants.value.unshift(response.data)
        return { success: true, data: response.data }
      } else {
        error.value = response.error?.message || 'Failed to create assistant'
        return { success: false, error: error.value }
      }
    } catch (err) {
      error.value = 'An unexpected error occurred'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  const updateAssistant = async (id: string, updates: Partial<CreateAssistantData>) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiClient.patch<Assistant>(`/assistants/${id}`, updates)
      
      if (response.success && response.data) {
        // Update in list
        const index = assistants.value.findIndex(a => a.id === id)
        if (index !== -1) {
          assistants.value[index] = response.data
        }
        
        // Update current if it's the same
        if (currentAssistant.value?.id === id) {
          currentAssistant.value = response.data
        }
        
        return { success: true, data: response.data }
      } else {
        error.value = response.error?.message || 'Failed to update assistant'
        return { success: false, error: error.value }
      }
    } catch (err) {
      error.value = 'An unexpected error occurred'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  const deleteAssistant = async (id: string) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiClient.delete(`/assistants/${id}`)
      
      if (response.success) {
        // Remove from list
        assistants.value = assistants.value.filter(a => a.id !== id)
        
        // Clear current if it's the same
        if (currentAssistant.value?.id === id) {
          currentAssistant.value = null
        }
        
        return { success: true }
      } else {
        error.value = response.error?.message || 'Failed to delete assistant'
        return { success: false, error: error.value }
      }
    } catch (err) {
      error.value = 'An unexpected error occurred'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  const uploadFile = async (assistantId: string, file: File, onProgress?: (progress: number) => void) => {
    isLoading.value = true
    error.value = null

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await apiClient.post<Assistant>(
        `/assistants/${assistantId}/files`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total && onProgress) {
              const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
              onProgress(progress)
            }
          },
        }
      )
      
      if (response.success && response.data) {
        // Update assistant in list
        const index = assistants.value.findIndex(a => a.id === assistantId)
        if (index !== -1) {
          assistants.value[index] = response.data
        }
        
        // Update current if it's the same
        if (currentAssistant.value?.id === assistantId) {
          currentAssistant.value = response.data
        }
        
        return { success: true, data: response.data }
      } else {
        error.value = response.error?.message || 'Failed to upload file'
        return { success: false, error: error.value }
      }
    } catch (err) {
      error.value = 'An unexpected error occurred'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  const deleteFile = async (assistantId: string, fileId: string) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiClient.delete<Assistant>(
        `/assistants/${assistantId}/files/${fileId}`
      )
      
      if (response.success && response.data) {
        // Update assistant in list
        const index = assistants.value.findIndex(a => a.id === assistantId)
        if (index !== -1) {
          assistants.value[index] = response.data
        }
        
        // Update current if it's the same
        if (currentAssistant.value?.id === assistantId) {
          currentAssistant.value = response.data
        }
        
        return { success: true, data: response.data }
      } else {
        error.value = response.error?.message || 'Failed to delete file'
        return { success: false, error: error.value }
      }
    } catch (err) {
      error.value = 'An unexpected error occurred'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  return {
    // State
    assistants,
    currentAssistant,
    isLoading,
    error,
    totalCount,
    
    // Getters
    assistantsList,
    assistantsCount,
    getAssistantById,
    
    // Actions
    fetchAssistants,
    fetchAssistant,
    createAssistant,
    updateAssistant,
    deleteAssistant,
    uploadFile,
    deleteFile,
  }
})