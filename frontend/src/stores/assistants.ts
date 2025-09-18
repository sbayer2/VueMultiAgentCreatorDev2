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
  const getAssistantById = computed(() => (id: number) => 
    assistants.value.find(a => a.id === id)
  )
  const getAssistantByAssistantId = computed(() => (assistant_id: string) => 
    assistants.value.find(a => a.assistant_id === assistant_id)
  )

  const getAssistantFileDetails = computed(() => {
    return (assistant: Assistant | null) => {
      if (!assistant || !assistant.file_ids) {
        return [];
      }
      // This is a placeholder. We need a central place to get file metadata.
      // For now, we'll just return objects with file_id.
      // TODO: Create a file metadata store.
      return assistant.file_ids.map(id => ({ file_id: id, original_name: `File ${id.slice(-6)}` }));
    };
  });

  // Actions
  const fetchAssistants = async () => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiClient.get<Assistant[]>('/assistants/')
      
      if (response.success && response.data) {
        assistants.value = response.data
        totalCount.value = response.data.length
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

  const fetchAssistant = async (assistant_id: string) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiClient.get<Assistant>(`/assistants/${assistant_id}`)

      if (response.success && response.data) {
        currentAssistant.value = response.data

        // Update in list if exists
        const index = assistants.value.findIndex(a => a.assistant_id === assistant_id)
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
      const response = await apiClient.post<Assistant>('/assistants/', data)
      
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

  const updateAssistant = async (assistant_id: string, updates: Partial<CreateAssistantData>) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiClient.put<Assistant>(`/assistants/${assistant_id}`, updates)
      
      if (response.success && response.data) {
        // Update in list
        const index = assistants.value.findIndex(a => a.assistant_id === assistant_id)
        if (index !== -1) {
          assistants.value[index] = response.data
        }
        
        // Update current if it's the same
        if (currentAssistant.value?.assistant_id === assistant_id) {
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

  const deleteAssistant = async (assistant_id: string) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiClient.delete(`/assistants/${assistant_id}`)
      
      if (response.success) {
        // Remove from list
        assistants.value = assistants.value.filter(a => a.assistant_id !== assistant_id)
        
        // Clear current if it's the same
        if (currentAssistant.value?.assistant_id === assistant_id) {
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

  const removeFileFromAssistant = async (assistantId: string, fileId: string) => {
    isLoading.value = true;
    error.value = null;
    try {
      const response = await apiClient.delete(`/assistants/${assistantId}/files/${fileId}`);
      if (response.success) {
        await fetchAssistant(assistantId);
        return { success: true };
      } else {
        error.value = response.error?.message || 'Failed to remove file';
        return { success: false, error: error.value };
      }
    } catch (err: any) {
      error.value = err.message || 'An unexpected error occurred';
      return { success: false, error: error.value };
    } finally {
      isLoading.value = false;
    }
  }

  const clearError = () => {
    error.value = null
  }

  const resetState = () => {
    assistants.value = []
    currentAssistant.value = null
    isLoading.value = false
    error.value = null
    totalCount.value = 0
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
    getAssistantByAssistantId,
    
    // Actions
    fetchAssistants,
    fetchAssistant,
    createAssistant,
    updateAssistant,
    deleteAssistant,
    clearError,
    resetState,
    removeFileFromAssistant,
  }
})

