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

// Assistant types
export interface Assistant {
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

export interface CreateAssistantData {
  name: string
  description: string
  model: string
  systemPrompt: string
  temperature?: number
  maxTokens?: number
  topP?: number
  frequencyPenalty?: number
  presencePenalty?: number
}

// Chat types
export interface ChatSession {
  id: string
  assistantId: string
  userId: string
  title: string
  messages: Message[]
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

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  metadata?: {
    files?: MessageFile[]
    [key: string]: any
  }
}

export interface SendMessageData {
  sessionId: string
  content: string
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

// WebSocket types for chat streaming
export interface StreamMessageStart {
  type: 'start'
  messageId: string
  sessionId: string
}

export interface StreamMessageToken {
  type: 'token'
  content: string
  messageId: string
}

export interface StreamMessageEnd {
  type: 'end'
  messageId: string
  fullContent: string
}

export interface StreamMessageError {
  type: 'error'
  error: string
  messageId?: string
}

export type StreamMessage = 
  | StreamMessageStart 
  | StreamMessageToken 
  | StreamMessageEnd 
  | StreamMessageError