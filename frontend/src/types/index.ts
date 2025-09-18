// User types
export interface User {
  id: string
  email: string
  name: string
  avatarUrl?: string
  createdAt: string
  updatedAt: string
}

// Authentication types
export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData extends LoginCredentials {
  name: string
  confirmPassword: string
}

export interface AuthResponse {
  user: User
  token: string
}

// Assistant Tools Configuration (OpenAI Assistants Beta v2)
export interface AssistantToolConfig {
  file_search: boolean
  code_interpreter: boolean
  vector_store_ids?: string[]
}

// Primary Assistant types (Assistants API)
export interface Assistant {
  id: number
  assistant_id: string
  name: string
  description?: string
  instructions: string
  model: string
  file_ids: string[]
  thread_id?: string
  tools: AssistantToolConfig
  conversation_count: number
  created_at: string
}

export interface CreateAssistantData {
  name: string
  description?: string
  instructions: string
  model: string
  file_ids?: string[]
}

export interface UpdateAssistantData {
  name?: string
  description?: string
  instructions?: string
  model?: string
  file_ids?: string[]
  tools?: AssistantToolConfig
}

// Legacy Assistant types (for migration)
export interface LegacyAssistant {
  id: string
  name: string
  description: string
  model: string
  systemPrompt: string
  temperature: number
  maxTokens: number
  topP: number
  frequencyPenalty: number
  presencePenalty: number
  files: AssistantFile[]
  createdBy: string
  createdAt: string
  updatedAt: string
}

export interface AssistantFile {
  id: string
  name: string
  size: number
  type: string
  uploadedAt: string
}

// Model and Tool information
export interface AvailableModel {
  id: string
  name: string
  description?: string
}

export interface AvailableTool {
  name: string
  description: string
  pricing: string
}

// Modern Chat types (Responses API)
export interface Conversation {
  id: number
  assistant_id: number
  title?: string
  message_count: number
  created_at: string
  updated_at?: string
  thread_id?: string // Thread ID for backend integration
}

export interface ConversationMessage {
  id: number
  role: 'user' | 'assistant' | 'system'
  content: string | MessageContent[]
  tool_calls?: ToolCall[]
  tokens_used?: number
  created_at: string
  attachments?: ImageAttachment[]
}

export interface ToolCall {
  id: string
  type: string
  function?: {
    name: string
    arguments: string
  }
}

export interface ChatResponse {
  message_id: number
  conversation_id: number
  content: string
  tool_calls?: ToolCall[]
  tokens_used?: number
  response_id?: string
}

export interface CreateConversationData {
  assistant_id: number
  title?: string
}

export interface SendMessageData {
  content: string | MessageContent[]
  assistant_id: number
  conversation_id?: number
  attachments?: ImageAttachment[]
}

// Legacy Chat types (for migration)
export interface LegacyChatSession {
  id: string
  assistantId: string
  userId: string
  title: string
  messages: LegacyMessage[]
  createdAt: string
  updatedAt: string
}

export interface MessageFile {
  id: string
  name: string
  size: number
  type: string
  url?: string
}

// Image attachment types
export interface ImageAttachment {
  id: string
  file_id: string
  name: string
  size: number
  type: string
  url?: string
  preview_url?: string
  width?: number
  height?: number
  uploaded_at: string
}

export interface ImageUploadStatus {
  id: string
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error'
  error?: string
  result?: ImageAttachment
}

// Content types for multi-modal messages
export interface TextContent {
  type: 'text'
  text: string
}

export interface ImageContent {
  type: 'image_file'
  image_file: {
    file_id: string
  }
}

export type MessageContent = TextContent | ImageContent

export interface LegacyMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  metadata?: {
    files?: MessageFile[]
    [key: string]: any
  }
}

// API Response types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: ApiError
}

export interface ApiError {
  code: string
  message: string
  details?: Record<string, any>
}

// Pagination types
export interface PaginationParams {
  page: number
  limit: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  totalPages: number
}

// File upload types
export interface FileUploadProgress {
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'completed' | 'error'
  error?: string
}

// WebSocket types for chat streaming (Responses API)
export interface StreamConnectionMessage {
  type: 'connection'
  status: 'connected'
  conversation_id: number
  message_count: number
}

export interface StreamTextDelta {
  type: 'text_delta'
  content: string
}

export interface StreamCompleteMessage {
  type: 'complete'
  content: string
  response_id?: string
}

export interface StreamErrorMessage {
  type: 'error'
  message: string
}

export interface StreamToolMessage {
  type: 'tool_call_start' | 'tool_call_delta' | 'tool_call_complete'
  tool_name?: string
  content?: string
}

export type StreamMessage = 
  | StreamConnectionMessage 
  | StreamTextDelta 
  | StreamCompleteMessage 
  | StreamErrorMessage 
  | StreamToolMessage

// Legacy WebSocket types (for migration)
export interface LegacyStreamMessageStart {
  type: 'start'
  messageId: string
  sessionId: string
}

export interface LegacyStreamMessageToken {
  type: 'token'
  content: string
  messageId: string
}

export interface LegacyStreamMessageEnd {
  type: 'end'
  messageId: string
  fullContent: string
}

export interface LegacyStreamMessageError {
  type: 'error'
  error: string
  messageId?: string
}

export type LegacyStreamMessage = 
  | LegacyStreamMessageStart 
  | LegacyStreamMessageToken 
  | LegacyStreamMessageEnd 
  | LegacyStreamMessageError