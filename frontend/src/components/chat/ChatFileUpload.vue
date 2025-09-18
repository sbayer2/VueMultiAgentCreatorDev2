<template>
  <div class="chat-file-upload">
    <button
      type="button"
      @click="triggerFileInput"
      :class="[
        'p-2 rounded-lg transition-colors',
        uploadedFiles.length > 0
          ? 'text-blue-600 bg-blue-100 hover:bg-blue-200'
          : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
      ]"
      :title="uploadType === 'image' ? 'Upload images' : 'Upload documents'"
    >
      <svg v-if="uploadType === 'image'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
      </svg>
      <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"/>
      </svg>
    </button>

    <input
      ref="fileInput"
      type="file"
      multiple
      :accept="acceptedFileTypes"
      @change="handleFileSelect"
      class="hidden"
    />

    <!-- Previews -->
    <div v-if="uploadedFiles.length > 0" class="mt-2 flex flex-wrap gap-2">
      <div v-for="file in uploadedFiles" :key="file.id" class="relative">
        <div class="w-16 h-16 rounded-lg border overflow-hidden flex items-center justify-center bg-gray-100">
          <img v-if="file.preview_url" :src="file.preview_url" class="w-full h-full object-cover" />
          <svg v-else class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
        </div>
        <button @click="removeFile(file.id)" class="absolute -top-1 -right-1 bg-red-500 text-white rounded-full p-0.5">
          <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { apiClient } from '@/utils/api';
import type { ImageAttachment } from '@/types';

const props = defineProps<{
  uploadType: 'image' | 'document';
  assistantId?: string;
}>();

const emit = defineEmits<{
  (e: 'images-changed', files: ImageAttachment[]): void;
  (e: 'file-uploaded', file: ImageAttachment): void;
}>();

const fileInput = ref<HTMLInputElement | null>(null);
const uploadedFiles = ref<ImageAttachment[]>([]);
const isUploading = ref(false);

const acceptedFileTypes = computed(() => {
  if (props.uploadType === 'image') {
    return 'image/jpeg,image/png,image/gif,image/webp';
  }
  return '.pdf,.txt,.csv,.json,.doc,.docx';
});

const triggerFileInput = () => {
  fileInput.value?.click();
};

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files) {
    uploadFiles(Array.from(target.files));
  }
};

const uploadFiles = async (files: File[]) => {
  isUploading.value = true;
  for (const file of files) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('purpose', props.uploadType === 'image' ? 'vision' : 'assistants');
    if (props.assistantId) {
      formData.append('assistant_id', props.assistantId);
    }

    const response = await apiClient.post('/files/upload-for-assistant', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });

    if (response.success) {
      const newFile: ImageAttachment = {
        id: response.data.file_id,
        file_id: response.data.file_id,
        name: response.data.filename,
        size: response.data.size,
        type: file.type,
        uploaded_at: new Date().toISOString(),
        preview_url: props.uploadType === 'image' ? URL.createObjectURL(file) : undefined,
      };
      uploadedFiles.value.push(newFile);
      emit('file-uploaded', newFile);
    }
  }
  isUploading.value = false;
  emit('images-changed', uploadedFiles.value);
};

const removeFile = (fileId: string) => {
  uploadedFiles.value = uploadedFiles.value.filter(f => f.id !== fileId);
  emit('images-changed', uploadedFiles.value);
};

const clearImages = () => {
  uploadedFiles.value = [];
  emit('images-changed', []);
};

defineExpose({ clearImages });
</script>
