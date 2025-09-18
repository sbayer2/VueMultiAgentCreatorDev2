<template>
  <div class="tool-selector">
    <h3 class="text-lg font-semibold mb-4">Built-in Tools</h3>
    <p class="text-gray-600 text-sm mb-4">
      Select which built-in tools your assistant can use. These tools provide enhanced capabilities without requiring custom code.
    </p>
    
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">

      <!-- File Search -->
      <div class="tool-option">
        <label class="flex items-start space-x-3 p-4 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
               :class="{ 'border-blue-500 bg-blue-50': modelValue.file_search }">
          <input
            type="checkbox"
            :checked="modelValue.file_search"
            @change="updateTool('file_search', $event.target.checked)"
            class="mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <div class="flex-1">
            <h4 class="font-medium text-gray-900">File Search</h4>
            <p class="text-sm text-gray-600 mt-1">
              Search and analyze uploaded documents and files
            </p>
            <div class="flex items-center mt-2 text-xs text-blue-600">
              <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
              </svg>
              RAG-powered document search
            </div>
          </div>
        </label>
      </div>

      <!-- Code Interpreter -->
      <div class="tool-option">
        <label class="flex items-start space-x-3 p-4 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
               :class="{ 'border-blue-500 bg-blue-50': modelValue.code_interpreter }">
          <input
            type="checkbox"
            :checked="modelValue.code_interpreter"
            @change="updateTool('code_interpreter', $event.target.checked)"
            class="mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <div class="flex-1">
            <h4 class="font-medium text-gray-900">Code Interpreter</h4>
            <p class="text-sm text-gray-600 mt-1">
              Execute Python code and perform data analysis tasks
            </p>
            <div class="flex items-center mt-2 text-xs text-blue-600">
              <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z" clip-rule="evenodd"/>
              </svg>
              Python execution sandbox
            </div>
          </div>
        </label>
      </div>

    </div>

    <!-- Vector Store Configuration (when file_search is enabled) -->
    <div v-if="modelValue.file_search" class="mt-6 p-4 border rounded-lg bg-blue-50">
      <h4 class="font-medium text-gray-900 mb-2">Vector Store Configuration</h4>
      <p class="text-sm text-gray-600 mb-3">
        Configure which vector stores this assistant can search. Leave empty to create a new one.
      </p>
      
      <div class="space-y-2">
        <label class="text-sm font-medium text-gray-700">Vector Store IDs (optional)</label>
        <textarea
          :value="vectorStoreIds"
          @input="updateVectorStores($event.target.value)"
          placeholder="vs-123abc, vs-456def (comma-separated)"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          rows="3"
        ></textarea>
        <p class="text-xs text-gray-500">
          Enter existing vector store IDs, separated by commas. A new vector store will be created if none are specified.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { AssistantToolConfig } from '@/types'

interface Props {
  modelValue: AssistantToolConfig
}

interface Emits {
  (e: 'update:modelValue', value: AssistantToolConfig): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()


const vectorStoreIds = computed(() => 
  props.modelValue.vector_store_ids?.join(', ') || ''
)

const updateTool = (tool: keyof Omit<AssistantToolConfig, 'vector_store_ids'>, enabled: boolean) => {
  const newConfig = { ...props.modelValue, [tool]: enabled }
  
  // Clear vector store IDs if file_search is disabled
  if (tool === 'file_search' && !enabled) {
    newConfig.vector_store_ids = []
  }
  
  emit('update:modelValue', newConfig)
}

const updateVectorStores = (value: string) => {
  const ids = value
    .split(',')
    .map(id => id.trim())
    .filter(id => id.length > 0)
  
  emit('update:modelValue', {
    ...props.modelValue,
    vector_store_ids: ids
  })
}
</script>

<style scoped>
.tool-option input[type="checkbox"]:checked + div {
  @apply text-blue-900;
}

.tool-selector h4 {
  line-height: 1.2;
}
</style>