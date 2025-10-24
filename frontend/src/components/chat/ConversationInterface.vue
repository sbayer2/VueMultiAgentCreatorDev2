<template>
  <div class="conversation-interface flex flex-col h-full">
    <!-- Header -->
    <div class="flex-none border-b border-gray-200 p-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="p-2 bg-blue-100 rounded-lg">
            <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/></svg>
          </div>
          <div>
            <h2 class="font-semibold text-gray-900">{{ assistantName }}</h2>
            <p class="text-sm text-gray-500">Active Conversation</p>
          </div>
        </div>
        <div class="flex items-center space-x-2">
          <button @click="resetThread" :disabled="isResettingThread" class="px-3 py-2 text-sm bg-orange-100 text-orange-700 border border-orange-300 rounded-md hover:bg-orange-200 disabled:opacity-50">
            {{ isResettingThread ? 'Creating...' : 'New Thread' }}
          </button>
          <button @click="$emit('close')" class="p-2 text-gray-400 hover:text-gray-600 rounded-lg" title="Close Conversation">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Messages Area -->
    <div class="flex-1 overflow-hidden flex flex-col">
      <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-4">
        <div v-if="messages.length === 0 && !isSending" class="text-center py-8">
          <div class="p-4 bg-blue-50 border border-blue-200 rounded-lg max-w-md mx-auto">
            <p class="text-blue-800 font-medium">Start a conversation</p>
            <p class="text-blue-600 text-sm mt-1">Ask {{ assistantName }} anything to get started.</p>
          </div>
        </div>
        <ChatMessage v-for="(message, index) in messages" :key="message.id || `msg-${index}`" :message="message" />
        <div v-if="isSending" class="flex justify-start">
          <div class="flex items-center space-x-2 p-3 bg-gray-100 rounded-lg max-w-xs">
            <div class="flex space-x-1">
              <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
              <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
              <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
            </div>
            <span class="text-sm text-gray-500">{{ assistantName }} is thinking...</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Message Input -->
    <div class="flex-none border-t border-gray-200 p-4">
      <!-- Attached Files Pop-up -->
      <div v-if="isFileFolderOpen" class="mb-4">
        <AttachedFilesList ref="attachedFilesListComponent" :assistant="activeAssistant" @delete-file="handleDeleteFile" />
      </div>

      <!-- Delete Error Message -->
      <div v-if="deleteError" class="mb-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded p-2">
        {{ deleteError }}
      </div>

      <form @submit.prevent="handleSendMessage" class="relative">
        <div class="flex items-end space-x-2">
          <ChatFileUpload uploadType="image" :assistant-id="activeAssistant?.assistant_id" @images-changed="onImagesChanged" ref="imageUploadComponent" />
          <ChatFileUpload uploadType="document" :assistant-id="activeAssistant?.assistant_id" @file-uploaded="handleDocumentUploaded" />
          
          <!-- Folder Icon -->
          <button type="button" @click="isFileFolderOpen = !isFileFolderOpen" class="p-2 text-gray-400 hover:text-gray-600 rounded-lg">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"></path></svg>
          </button>

          <div class="flex-1 relative">
            <textarea
              ref="messageInput"
              v-model="newMessage"
              @keydown.enter.exact.prevent="handleSendMessage"
              @input="autoResizeTextarea"
              :disabled="isSending"
              class="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Type your message..."
              rows="1"
            ></textarea>
            <button type="submit" :disabled="!canSend" class="absolute right-2 bottom-2 p-2 text-blue-600 disabled:text-gray-400">
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z"/></svg>
            </button>
          </div>
        </div>
      </form>
      <div v-if="error" class="mt-2 text-sm text-red-600">{{ error }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch, onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import { useConversationsStore } from '@/stores/conversations';
import { useAssistantsStore } from '@/stores/assistants';
import type { ConversationMessage, ImageAttachment, Assistant } from '@/types';
import ChatMessage from './ChatMessage.vue';
import ChatFileUpload from './ChatFileUpload.vue';
import AttachedFilesList from './AttachedFilesList.vue';

interface Props {
  messages: ConversationMessage[];
  assistantName: string;
}
const props = defineProps<Props>();
const emit = defineEmits(['close']);

const conversationsStore = useConversationsStore();
const assistantsStore = useAssistantsStore();
const { isSending, error, activeAssistant } = storeToRefs(conversationsStore);

const newMessage = ref('');
const isResettingThread = ref(false);
const messagesContainer = ref<HTMLElement | null>(null);
const messageInput = ref<HTMLTextAreaElement | null>(null);
const imageUploadComponent = ref<InstanceType<typeof ChatFileUpload> | null>(null);
const attachedFilesListComponent = ref<InstanceType<typeof AttachedFilesList> | null>(null);
const attachedImages = ref<ImageAttachment[]>([]);
const isFileFolderOpen = ref(false);
const deleteError = ref<string | null>(null);

const canSend = computed(() => (newMessage.value.trim().length > 0 || attachedImages.value.length > 0) && !isSending.value);

const handleSendMessage = async () => {
  if (!canSend.value) return;
  const content = newMessage.value.trim();
  const attachments = [...attachedImages.value];
  newMessage.value = '';
  attachedImages.value = [];
  imageUploadComponent.value?.clearImages();
  autoResizeTextarea();
  await conversationsStore.sendMessage(content, attachments);
};

const resetThread = async () => {
  isResettingThread.value = true;
  await conversationsStore.createNewThreadForAssistant();
  if (activeAssistant.value) {
    await assistantsStore.fetchAssistant(activeAssistant.value.assistant_id);
  }
  isResettingThread.value = false;
};

const onImagesChanged = (images: ImageAttachment[]) => {
  attachedImages.value = images;
};

const handleDocumentUploaded = async (file: ImageAttachment) => {
  if (!activeAssistant.value) return;
  const currentFiles = activeAssistant.value.file_ids || [];
  const updatedFiles = [...new Set([...currentFiles, file.file_id])];
  await assistantsStore.updateAssistant(activeAssistant.value.assistant_id, {
    file_ids: updatedFiles,
  });
};

const handleDeleteFile = async (fileId: string) => {
  console.log(`DEBUG: handleDeleteFile called for ${fileId}`);
  deleteError.value = null;  // Clear any previous errors

  if (!activeAssistant.value) {
    console.log('DEBUG: No active assistant, aborting delete');
    deleteError.value = 'No active assistant selected';
    return;
  }

  if (confirm('Are you sure you want to permanently delete this file?')) {
    console.log(`DEBUG: User confirmed deletion of ${fileId}`);
    console.log(`DEBUG: Calling store to remove file from assistant ${activeAssistant.value.assistant_id}`);

    const result = await assistantsStore.removeFileFromAssistant(activeAssistant.value.assistant_id, fileId);

    if (result.success) {
      console.log(`DEBUG: File ${fileId} deleted successfully`);
      // Refresh the assistant data to get updated file list
      if (activeAssistant.value) {
        await assistantsStore.fetchAssistant(activeAssistant.value.assistant_id);
      }
      // Refresh the file list UI
      if (attachedFilesListComponent.value) {
        attachedFilesListComponent.value.refreshFiles();
      }
    } else {
      console.error(`DEBUG: Failed to delete file ${fileId}:`, result.error);
      deleteError.value = result.error || 'Failed to delete file. Please try again.';
      // Error will be displayed to user via deleteError ref
    }
  } else {
    console.log(`DEBUG: User cancelled deletion of ${fileId}`);
  }
};

const scrollToBottom = () => {
  nextTick(() => {
    messagesContainer.value?.scrollTo({ top: messagesContainer.value.scrollHeight, behavior: 'smooth' });
  });
};

const autoResizeTextarea = () => {
  if (messageInput.value) {
    messageInput.value.style.height = 'auto';
    const newHeight = Math.min(messageInput.value.scrollHeight, 120);
    messageInput.value.style.height = `${newHeight}px`;
  }
};

watch(() => props.messages, scrollToBottom, { deep: true });
onMounted(scrollToBottom);
</script>

<style scoped>
textarea { max-height: 120px; min-height: 44px; }
@keyframes bounce { 0%, 80%, 100% { transform: translateY(0); } 40% { transform: translateY(-6px); } }
.animate-bounce { animation: bounce 1.4s infinite; }
</style>
