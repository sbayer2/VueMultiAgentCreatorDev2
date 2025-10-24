<template>
  <div class="attached-files-list p-4 bg-gray-50 rounded-lg border">
    <h4 class="text-sm font-medium text-gray-900 mb-3">Attached Files</h4>
    <div v-if="isLoading" class="text-center text-sm text-gray-500 py-4">
      Loading files...
    </div>
    <div v-else-if="files.length === 0" class="text-center text-sm text-gray-500 py-4">
      No files attached.
    </div>
    <div v-else class="space-y-2 max-h-48 overflow-y-auto">
      <div
        v-for="file in files"
        :key="file.file_id"
        class="flex items-center justify-between p-2 bg-white border rounded-md"
      >
        <div class="flex items-center space-x-2 min-w-0">
          <svg class="w-5 h-5 text-gray-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
          <span class="text-sm text-gray-800 truncate" :title="file.filename">{{ file.filename }}</span>
        </div>
        <button
          @click="deleteFile(file.file_id)"
          class="p-1 text-red-500 hover:text-red-700 rounded-full hover:bg-red-50"
          title="Delete file"
        >
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import { apiClient } from '@/utils/api';
import type { Assistant } from '@/types';

interface FileInfo {
  file_id: string;
  filename: string;
  size: number;
  purpose: string;
}

const props = defineProps<{
  assistant: Assistant | null;
}>();

const emit = defineEmits(['delete-file']);

const files = ref<FileInfo[]>([]);
const isLoading = ref(false);

const fetchFileDetails = async () => {
  if (!props.assistant || !props.assistant.file_ids || props.assistant.file_ids.length === 0) {
    files.value = [];
    return;
  }

  isLoading.value = true;
  try {
    const response = await apiClient.post('/files/details', {
      file_ids: props.assistant.file_ids,
    });
    if (response.success) {
      files.value = response.data;
    } else {
      files.value = [];
    }
  } catch (error) {
    files.value = [];
  } finally {
    isLoading.value = false;
  }
};

// Delete file with optimistic UI update (will be restored by parent if delete fails)
const deleteFile = (fileId: string) => {
  console.log(`DEBUG: Deleting file ${fileId} from UI`);

  // Optimistic update - immediately remove from UI for better UX
  files.value = files.value.filter(f => f.file_id !== fileId);
  console.log(`DEBUG: File removed from UI optimistically`);

  // Emit event to parent to handle backend delete
  // Parent will refresh assistant data which will trigger watcher to restore files if delete failed
  console.log(`DEBUG: Emitting delete-file event for ${fileId}`);
  emit('delete-file', fileId);
};

watch(() => props.assistant?.file_ids, fetchFileDetails, { deep: true, immediate: true });

onMounted(fetchFileDetails);
</script>
