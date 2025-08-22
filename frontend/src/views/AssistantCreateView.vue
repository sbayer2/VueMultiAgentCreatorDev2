<template>
  <div class="assistant-create-view max-w-4xl mx-auto px-4 py-6">
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
        <h1 class="text-3xl font-bold text-gray-900">Create New Assistant</h1>
      </div>
      <p class="text-gray-600">
        Configure your AI assistant with custom instructions, model selection, and built-in tools.
      </p>
    </div>

    <!-- Form -->
    <form @submit.prevent="formHandleSubmit" class="space-y-8">
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
              :model-value="form.name"
              @update:model-value="setFieldValue('name', $event)"
              placeholder="e.g., Research Assistant"
              :error="errors.name"
              required
            />
            <p class="mt-1 text-sm text-gray-500">
              Choose a descriptive name for your assistant
            </p>
          </div>

          <!-- Model -->
          <div>
            <label for="model" class="block text-sm font-medium text-gray-700 mb-2">
              Model *
            </label>
            <select
              id="model"
              :value="form.model"
              @change="setFieldValue('model', ($event.target as HTMLSelectElement).value)"
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
            :model-value="form.description"
            @update:model-value="setFieldValue('description', $event)"
            placeholder="Brief description of what this assistant does"
            :error="errors.description"
          />
          <p class="mt-1 text-sm text-gray-500">
            Help others understand what this assistant is designed for
          </p>
        </div>
      </div>

      <!-- Instructions -->
      <div class="bg-white rounded-lg border border-gray-200 p-6">
        <h2 class="text-xl font-semibold text-gray-900 mb-4">Instructions</h2>
        <p class="text-gray-600 mb-4">
          Define how your assistant should behave and what it should focus on. These instructions guide the AI's responses and behavior.
        </p>
        
        <div>
          <label for="instructions" class="block text-sm font-medium text-gray-700 mb-2">
            System Instructions *
          </label>
          <textarea
            id="instructions"
            :value="form.instructions"
            @input="setFieldValue('instructions', ($event.target as HTMLTextAreaElement).value)"
            rows="8"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
            :class="{ 'border-red-500': errors.instructions }"
            placeholder="You are a helpful assistant specialized in..."
          ></textarea>
          <p v-if="errors.instructions" class="mt-1 text-sm text-red-600">{{ errors.instructions }}</p>
          
          <div class="mt-2 flex justify-between items-center">
            <p class="text-sm text-gray-500">
              Be specific about the assistant's role, expertise, and communication style
            </p>
            <span class="text-xs text-gray-400">
              {{ form.instructions.length }} characters
            </span>
          </div>
        </div>

        <!-- Quick Templates -->
        <div class="mt-4">
          <p class="text-sm font-medium text-gray-700 mb-2">Quick Start Templates:</p>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="template in instructionTemplates"
              :key="template.name"
              type="button"
              @click="applyTemplate(template)"
              class="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
            >
              {{ template.name }}
            </button>
          </div>
        </div>
      </div>

      <!-- File Upload (Optional) -->
      <div class="bg-white rounded-lg border border-gray-200 p-6">
        <h2 class="text-xl font-semibold text-gray-900 mb-4">File Attachments (Optional)</h2>
        <p class="text-gray-600 mb-4">
          Upload files that your assistant can reference and search through. Supports images for vision analysis and documents for knowledge base.
        </p>
        <FileUpload v-model="form.file_ids" />
      </div>

      <!-- Form Actions -->
      <div class="flex items-center justify-between pt-6 border-t">
        <button
          type="button"
          @click="$router.go(-1)"
          class="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
        >
          Cancel
        </button>
        
        <BaseButton
          type="submit"
          :loading="isLoading"
          class="px-6 py-2"
        >
          Create Assistant
        </BaseButton>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAssistantsStore } from '@/stores/assistants'
import { useForm } from '@/composables/useForm'
import type { CreateAssistantData } from '@/types'
import BaseInput from '@/components/common/BaseInput.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import FileUpload from '@/components/assistant/FileUpload.vue'

const router = useRouter()
const assistantsStore = useAssistantsStore()

// Form data
const initialFormData: CreateAssistantData = {
  name: '',
  description: '',
  instructions: '',
  model: 'gpt-4o-mini',
  file_ids: []
}

const validationRules = {
  name: [(value: string) => {
    if (!value.trim()) return 'Assistant name is required'
    if (value.length < 2) return 'Name must be at least 2 characters'
    if (value.length > 100) return 'Name cannot exceed 100 characters'
    return true
  }],
  model: [(value: string) => {
    if (!value) return 'Please select a model'
    return true
  }],
  instructions: [(value: string) => {
    if (!value.trim()) return 'Instructions are required'
    if (value.length < 10) return 'Instructions must be at least 10 characters'
    if (value.length > 32000) return 'Instructions cannot exceed 32,000 characters'
    return true
  }],
  description: [(value: string) => {
    if (value && value.length > 500) return 'Description cannot exceed 500 characters'
    return true
  }]
}

const { 
  values: form, 
  errors, 
  isSubmitting: isLoading, 
  validateAllFields,
  setFieldValue,
  setFieldError,
  handleSubmit: formHandleSubmit
} = useForm({
  initialValues: initialFormData,
  rules: validationRules,
  onSubmit: async (values) => {
    const result = await assistantsStore.createAssistant(values)
    
    if (result.success) {
      router.push({ name: 'assistants' })
    } else {
      console.error('Failed to create assistant:', result.error)
    }
  }
})

// Instruction templates for quick start
const instructionTemplates = ref([
  {
    name: 'Research Assistant',
    content: 'You are a knowledgeable research assistant specialized in finding, analyzing, and summarizing information from various sources. You help users conduct thorough research by searching for relevant information, evaluating sources for credibility, and presenting findings in a clear, organized manner. Always cite your sources and distinguish between facts and analysis.'
  },
  {
    name: 'Code Helper',
    content: 'You are an expert programming assistant that helps with code development, debugging, and optimization. You can work with multiple programming languages and are skilled at explaining complex concepts clearly. When helping with code, always provide working examples, explain your reasoning, and suggest best practices. You can execute and test code when needed.'
  },
  {
    name: 'Writing Assistant',
    content: 'You are a professional writing assistant that helps with creating, editing, and improving various types of written content. You excel at adapting your writing style to different audiences and purposes, from academic papers to creative writing to business communications. You provide constructive feedback and suggestions for improvement while maintaining the author\'s voice.'
  },
  {
    name: 'Data Analyst',
    content: 'You are a data analysis expert skilled in statistical analysis, data visualization, and pattern recognition. You help users understand their data through exploratory analysis, create meaningful visualizations, and draw actionable insights. You can work with various data formats and use appropriate statistical methods to answer business questions.'
  }
])

const applyTemplate = (template: { name: string; content: string }) => {
  setFieldValue('instructions', template.content)
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

</script>

<style scoped>
/* Custom styles for form elements */
textarea {
  resize: vertical;
  min-height: 120px;
}

select:focus {
  outline: none;
}

/* Animation for template buttons */
.bg-gray-100 {
  transition: all 0.2s ease;
}

/* Make instruction textarea more code-friendly */
#instructions {
  line-height: 1.5;
  tab-size: 2;
}
</style>