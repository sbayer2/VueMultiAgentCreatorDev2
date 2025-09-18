<template>
  <div class="assistant-edit-view max-w-4xl mx-auto px-4 py-6">
    <!-- Loading State -->
    <div v-if="isLoadingAssistant" class="text-center py-12">
      <LoadingSpinner size="large" />
      <p class="text-gray-500 mt-4">Loading assistant...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="loadError" class="text-center py-12">
      <div class="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md mx-auto">
        <svg class="w-8 h-8 text-red-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 15.5c-.77.833.192 2.5 1.732 2.5z"/>
        </svg>
        <h3 class="text-lg font-medium text-red-800 mb-2">Failed to Load Assistant</h3>
        <p class="text-red-600 mb-4">{{ loadError }}</p>
        <div class="space-x-3">
          <button
            @click="loadAssistant"
            class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
          >
            Try Again
          </button>
          <button
            @click="$router.go(-1)"
            class="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div v-else-if="assistant">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex items-center mb-2">
          <button 
            @click="$router.go(-1)"
            class="mr-4 p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
            </svg>
          </button>
          <h1 class="text-3xl font-bold text-gray-900">Edit Assistant</h1>
        </div>
        <p class="text-gray-600">
          Update your AI assistant's configuration, instructions, and enabled tools.
        </p>
      </div>

      <!-- Form -->
      <form @submit.prevent="handleSubmit" class="space-y-8">
        <!-- Basic Information -->
        <div class="bg-white rounded-lg border border-gray-200 p-6">
          <h2 class="text-xl font-semibold text-gray-900 mb-4">Basic Information</h2>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Name -->
            <div>
              <label for="name" class="block text-sm font-medium text-gray-700 mb-2">
                Assistant Name *
              </label>
              <BaseInput
                id="name"
                v-model="form.name"
                placeholder="e.g., Research Assistant"
                :error="errors.name"
                required
              />
            </div>

            <!-- Model -->
            <div>
              <label for="model" class="block text-sm font-medium text-gray-700 mb-2">
                Model *
              </label>
              <select
                id="model"
                v-model="form.model"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                :class="{ 'border-red-500': errors.model }"
              >
                <option value="">Select a model</option>
                <optgroup label="GPT-4.1 Models (Latest)">
                  <option value="gpt-4.1-2025-04-14">GPT-4.1 (Latest Full)</option>
                  <option value="gpt-4.1-mini-2025-04-01">GPT-4.1 Mini (Latest Cost-effective)</option>
                </optgroup>
                <optgroup label="GPT-4 Models">
                  <option value="gpt-4o">GPT-4o (Recommended)</option>
                  <option value="gpt-4o-mini">GPT-4o Mini (Cost-effective)</option>
                  <option value="gpt-4-turbo">GPT-4 Turbo</option>
                  <option value="gpt-4">GPT-4</option>
                </optgroup>
                <optgroup label="GPT-3.5 Models">
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                </optgroup>
              </select>
              <p v-if="errors.model" class="mt-1 text-sm text-red-600">{{ errors.model }}</p>
              <p class="mt-1 text-sm text-gray-500">
                {{ getModelDescription(form.model) }}
              </p>
            </div>
          </div>

          <!-- Description -->
          <div class="mt-6">
            <label for="description" class="block text-sm font-medium text-gray-700 mb-2">
              Description (Optional)
            </label>
            <BaseInput
              id="description"
              v-model="form.description"
              placeholder="Brief description of what this assistant does"
              :error="errors.description"
            />
          </div>
        </div>

        <!-- Instructions -->
        <div class="bg-white rounded-lg border border-gray-200 p-6">
          <h2 class="text-xl font-semibold text-gray-900 mb-4">Instructions</h2>
          
          <div>
            <label for="instructions" class="block text-sm font-medium text-gray-700 mb-2">
              System Instructions *
            </label>
            <textarea
              id="instructions"
              v-model="form.instructions"
              rows="8"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
              :class="{ 'border-red-500': errors.instructions }"
              placeholder="You are a helpful assistant specialized in..."
            ></textarea>
            <p v-if="errors.instructions" class="mt-1 text-sm text-red-600">{{ errors.instructions }}</p>
            
            <div class="mt-2 flex justify-between items-center">
              <p class="text-sm text-gray-500">
                Define how your assistant should behave and respond
              </p>
              <span class="text-xs text-gray-400">
                {{ form.instructions.length }} characters
              </span>
            </div>
          </div>
        </div>

        <!-- Tools Configuration -->
        <div class="bg-white rounded-lg border border-gray-200 p-6">
          <ToolSelector v-model="form.tools" />
        </div>

        <!-- Form Actions -->
        <div class="flex items-center justify-between pt-6 border-t">
          <div class="flex space-x-3">
            <button
              type="button"
              @click="$router.go(-1)"
              class="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
            >
              Cancel
            </button>
            
            <button
              type="button"
              @click="resetForm"
              class="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
            >
              Reset Changes
            </button>
          </div>
          
          <BaseButton
            type="submit"
            :loading="isLoading"
            class="px-6 py-2"
            :disabled="!hasChanges"
          >
            {{ hasChanges ? 'Update Assistant' : 'No Changes' }}
          </BaseButton>
        </div>
      </form>

      <!-- Conversation History -->
      <div class="mt-12 bg-white rounded-lg border border-gray-200 p-6">
        <h2 class="text-xl font-semibold text-gray-900 mb-4">Conversation History</h2>
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-600">
              This assistant has <strong>{{ assistant.conversation_count }}</strong> conversations
            </p>
            <p class="text-sm text-gray-500 mt-1">
              Created {{ formatDate(assistant.created_at) }}
              <span v-if="assistant.updated_at">• Last updated {{ formatDate(assistant.updated_at) }}</span>
            </p>
          </div>
          <router-link
            :to="`/dashboard/chat`"
            class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
            </svg>
            Start New Chat
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAssistantsStore } from '@/stores/assistants'
import { useForm } from '@/composables/useForm'
import type { UpdateAssistantData, AssistantToolConfig, Assistant } from '@/types'
import BaseInput from '@/components/common/BaseInput.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ToolSelector from '@/components/assistant/ToolSelector.vue'

interface Props {
  id: string
}

const props = defineProps<Props>()
const route = useRoute()
const router = useRouter()
const assistantsStore = useAssistantsStore()

// State
const assistant = ref<Assistant | null>(null)
const isLoadingAssistant = ref(false)
const loadError = ref<string | null>(null)
const originalData = ref<UpdateAssistantData | null>(null)

// Get assistant ID from route params
const assistantId = computed(() => {
  return props.id || route.params.id as string
})

// Form setup
const {
  values: form,
  errors,
  isSubmitting: isLoading,
  validateAllFields: validate,
  reset: resetFormData,
  setFieldValue
} = useForm<UpdateAssistantData>({
  initialValues: {
    name: '',
    description: '',
    instructions: '',
    model: 'gpt-4o-mini',
    tools: {
      file_search: false,
      code_interpreter: false,
      vector_store_ids: []
    }
  },
  rules: {
    name: [(value: string) => {
      if (!value?.trim()) return 'Assistant name is required'
      if (value.length < 2) return 'Name must be at least 2 characters'
      if (value.length > 100) return 'Name cannot exceed 100 characters'
      return true
    }],
    model: [(value: string) => {
      if (!value) return 'Please select a model'
      return true
    }],
    instructions: [(value: string) => {
      if (!value?.trim()) return 'Instructions are required'
      if (value.length < 10) return 'Instructions must be at least 10 characters'
      if (value.length > 32000) return 'Instructions cannot exceed 32,000 characters'
      return true
    }],
    description: [(value?: string) => {
      if (value && value.length > 500) return 'Description cannot exceed 500 characters'
      return true
    }],
    tools: [(value: any) => {
      // Tools validation - just ensure it's an object
      if (!value || typeof value !== 'object') return 'Invalid tools configuration'
      return true
    }]
  }
})

// Computed
const hasChanges = computed(() => {
  if (!originalData.value) return false
  
  return (
    form.name !== originalData.value.name ||
    form.description !== originalData.value.description ||
    form.instructions !== originalData.value.instructions ||
    form.model !== originalData.value.model ||
    JSON.stringify(form.tools) !== JSON.stringify(originalData.value.tools)
  )
})

// Methods
const loadAssistant = async () => {
  console.log('DEBUG: loadAssistant called', { assistantId: assistantId.value })
  if (!assistantId.value) {
    loadError.value = 'Invalid assistant ID'
    console.log('DEBUG: No assistant ID found')
    return
  }

  isLoadingAssistant.value = true
  loadError.value = null

  try {
    console.log('DEBUG: Calling fetchAssistant', assistantId.value)
    const result = await assistantsStore.fetchAssistant(assistantId.value)
    
    if (result.success && result.data) {
      console.log('DEBUG: Assistant data received:', result.data)
      assistant.value = result.data

      // Populate form with assistant data
      const assistantData: UpdateAssistantData = {
        name: result.data.name,
        description: result.data.description || '',
        instructions: result.data.instructions,
        model: result.data.model,
        tools: result.data.tools
      }

      console.log('DEBUG: Prepared assistantData for form:', assistantData)

      // Store original data for change detection
      originalData.value = JSON.parse(JSON.stringify(assistantData))

      // Update form using setFieldValue
      console.log('DEBUG: Form before assignment:', form.value)
      setFieldValue('name', assistantData.name)
      setFieldValue('description', assistantData.description)
      setFieldValue('instructions', assistantData.instructions)
      setFieldValue('model', assistantData.model)
      setFieldValue('tools', assistantData.tools)
      console.log('DEBUG: Form after assignment:', form.value)
    } else {
      loadError.value = result.error || 'Failed to load assistant'
    }
  } catch (error) {
    loadError.value = 'An unexpected error occurred'
    console.error('Failed to load assistant:', error)
  } finally {
    isLoadingAssistant.value = false
  }
}

const resetForm = () => {
  if (originalData.value) {
    Object.assign(form, JSON.parse(JSON.stringify(originalData.value)))
    resetFormData()
  }
}

const handleSubmit = async () => {
  console.log('DEBUG: handleSubmit called')
  console.log('DEBUG: assistantId:', assistantId.value)
  console.log('DEBUG: hasChanges:', hasChanges.value)
  console.log('DEBUG: form.value:', form.value)

  try {
    console.log('DEBUG: Calling validate()')
    console.log('DEBUG: Form errors before validation:', errors.value)
    const isValid = validate()
    console.log('DEBUG: Validation result:', isValid)
    console.log('DEBUG: Form errors after validation:', errors.value)

    if (!isValid || !assistantId.value || !hasChanges.value) {
      console.log('DEBUG: Validation failed or no changes')
      console.log('DEBUG: isValid:', isValid, 'assistantId:', assistantId.value, 'hasChanges:', hasChanges.value)
      return
    }

    console.log('DEBUG: Calling updateAssistant with:', assistantId.value, form.value)
    const result = await assistantsStore.updateAssistant(assistantId.value, form.value)
    console.log('DEBUG: Update result:', result)

    if (result.success) {
      // Update original data to reflect saved state
      originalData.value = JSON.parse(JSON.stringify(form.value))

      // Navigate back to assistants list
      router.push('/dashboard/assistants')
    } else {
      console.error('DEBUG: Update failed:', result.error)
    }
  } catch (error) {
    console.error('DEBUG: Exception in handleSubmit:', error)
  }
}

const getModelDescription = (model: string): string => {
  const descriptions: Record<string, string> = {
    'gpt-4.1-2025-04-14': 'Latest GPT-4.1 model with enhanced capabilities and reasoning',
    'gpt-4.1-mini-2025-04-01': 'Latest cost-effective mini model with improved performance',
    'gpt-4o': 'Most capable model with vision, best for complex tasks',
    'gpt-4o-mini': 'Cost-effective option with good performance',
    'gpt-4-turbo': 'Fast and capable, good balance of performance and speed',
    'gpt-4': 'Original GPT-4, highly capable for complex reasoning',
    'gpt-3.5-turbo': 'Fast and affordable, good for simpler tasks'
  }
  return descriptions[model] || 'Select a model to see description'
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit'
  })
}

// Initialize
onMounted(() => {
  console.log('DEBUG: AssistantEditView mounted', { assistantId: assistantId.value, routeParams: route.params })
  loadAssistant()
})

// Handle route changes (if navigating between edit views)
watch(() => route.params.id, () => {
  if (route.name === 'assistant-edit') {
    loadAssistant()
  }
})
</script>

<style scoped>
textarea {
  resize: vertical;
  min-height: 120px;
}

select:focus {
  outline: none;
}

#instructions {
  line-height: 1.5;
  tab-size: 2;
}
</style>