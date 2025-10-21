import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { apiClient } from '@/utils/api';
import type {
  ConversationMessage,
  ImageAttachment,
  Assistant,
} from '@/types';

// This store is refactored to manage the state of the active chat session
// based on the legacy "one-thread-per-assistant" model.
export const useConversationsStore = defineStore('conversations', () => {
  // STATE
  const currentAssistant = ref<Assistant | null>(null);
  const currentMessages = ref<ConversationMessage[]>([]);
  const isLoading = ref(false);
  const isSending = ref(false);
  const error = ref<string | null>(null);
  const streamingContent = ref<string>('');

  // GETTERS
  const activeAssistant = computed(() => currentAssistant.value);
  const activeThreadMessages = computed(() => currentMessages.value);
  const isStreaming = computed(() => !!streamingContent.value);

  // ACTIONS

  /**
   * Selects an assistant to chat with, effectively starting or resuming a conversation.
   */
  const selectAssistantForChat = async (assistant: Assistant) => {
    if (currentAssistant.value?.id === assistant.id) {
      return; // Already selected
    }
    currentAssistant.value = assistant;
    currentMessages.value = []; // Clear previous messages
    error.value = null;

    // Fetch message history for this assistant's thread
    await loadThreadMessages(assistant.assistant_id);
  };

  /**
   * Loads message history from the assistant's thread.
   */
  const loadThreadMessages = async (assistantId: string) => {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await apiClient.get(`/chat/messages/${assistantId}`);

      if (response.success && response.data) {
        const { messages } = response.data;

        // Format messages for display
        const formattedMessages: ConversationMessage[] = messages.map((msg: any) => {
          let attachments: ImageAttachment[] | undefined;

          if (msg.attachments && msg.attachments.length > 0) {
            // Build absolute URLs to backend for image loading
            const apiBaseUrl = import.meta.env.VITE_API_URL || '/api'
            attachments = msg.attachments.map((att: any) => ({
              id: att.file_id,
              file_id: att.file_id,
              name: `image_${att.file_id.slice(-6)}.png`,
              size: 0,
              type: 'image_file',
              url: `${apiBaseUrl}/files/openai/${att.file_id}`,
              preview_url: `${apiBaseUrl}/files/openai/${att.file_id}`,
            }));
          }

          return {
            id: msg.id,
            role: msg.role,
            content: msg.content,
            created_at: msg.created_at,
            attachments,
          };
        });

        currentMessages.value = formattedMessages;
      } else {
        // No messages or error - start with empty array
        currentMessages.value = [];
      }
    } catch (err: any) {
      console.error('Failed to load thread messages:', err);
      error.value = err.message || 'Failed to load message history';
      currentMessages.value = [];
    } finally {
      isLoading.value = false;
    }
  };

  /**
   * Sends a message to the active assistant's thread.
   */
  const sendMessage = async (
    content: string,
    attachments?: ImageAttachment[]
  ) => {
    if (!currentAssistant.value) {
      error.value = 'No assistant selected.';
      return { success: false, error: error.value };
    }

    isSending.value = true;
    error.value = null;
    streamingContent.value = '';

    const userMessage: ConversationMessage = {
      id: Date.now(),
      role: 'user',
      content,
      created_at: new Date().toISOString(),
      attachments: attachments?.length ? attachments : undefined,
    };
    currentMessages.value.push(userMessage);

    try {
      const payload = {
        content,
        assistant_id: currentAssistant.value.assistant_id,
        file_ids: attachments?.map((att) => att.file_id) ?? [],
      };

      const response = await apiClient.post('/chat/message', payload);

      if (response.success && response.data) {
        const assistantResponse = response.data;
        let responseAttachments: ImageAttachment[] = [];

        if (assistantResponse.attachments) {
          responseAttachments = assistantResponse.attachments.map((att: any) => ({
            id: att.file_id,
            file_id: att.file_id,
            name: `image_${att.file_id.slice(-6)}.png`,
            size: 0,
            type: 'image_file',
            url: `/api/files/openai/${att.file_id}`,
            preview_url: `/api/files/openai/${att.file_id}`,
          }));
        }

        const assistantMessage: ConversationMessage = {
          id: assistantResponse.message_id,
          role: 'assistant',
          content: assistantResponse.content,
          created_at: new Date().toISOString(),
          attachments:
            responseAttachments.length > 0 ? responseAttachments : undefined,
        };
        currentMessages.value.push(assistantMessage);
        return { success: true, data: assistantMessage };
      } else {
        currentMessages.value.pop();
        error.value = response.error?.message || 'Failed to send message';
        return { success: false, error: error.value };
      }
    } catch (err: any) {
      currentMessages.value.pop();
      error.value = err.message || 'An unexpected error occurred';
      return { success: false, error: error.value };
    } finally {
      isSending.value = false;
    }
  };

  /**
   * Creates a new thread for the currently active assistant.
   */
  const createNewThreadForAssistant = async () => {
    if (!currentAssistant.value) {
      error.value = 'No assistant selected to create a new thread for.';
      return { success: false, error: error.value };
    }

    isLoading.value = true;
    error.value = null;

    try {
      const response = await apiClient.post('/chat/new-thread', {
        assistant_id: currentAssistant.value.assistant_id,
      });

      if (response.success) {
        currentMessages.value = [];
        return { success: true, data: response.data };
      } else {
        error.value =
          response.error?.message || 'Failed to create a new thread.';
        return { success: false, error: error.value };
      }
    } catch (err: any) {
      error.value =
        err.message ||
        'An unexpected error occurred while creating a new thread.';
      return { success: false, error: error.value };
    } finally {
      isLoading.value = false;
    }
  };

  const clearCurrentConversation = () => {
    currentAssistant.value = null;
    currentMessages.value = [];
    streamingContent.value = '';
  };

  return {
    // State
    currentAssistant,
    currentMessages,
    isLoading,
    isSending,
    error,
    streamingContent,
    // Getters
    activeAssistant,
    activeThreadMessages,
    isStreaming,
    // Actions
    selectAssistantForChat,
    sendMessage,
    createNewThreadForAssistant,
    clearCurrentConversation,
  };
});
