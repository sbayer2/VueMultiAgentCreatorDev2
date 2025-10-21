# System Architecture

## Technology Stack

### Frontend
- **Framework**: Vue 3 Composition API + TypeScript + Vite + Tailwind CSS + Pinia
- **Routing**: Vue Router with authentication guards
- **State**: Pinia stores with persisted state for auth and preferences
- **UI Components**: Headless UI + Heroicons for accessible components
- **Styling**: Tailwind CSS with custom design system

### Backend
- **Framework**: FastAPI + SQLAlchemy + MySQL
- **Authentication**: JWT tokens with bcrypt password hashing
- **Real-time**: WebSocket connections for live chat
- **Storage**: File uploads with OpenAI vector stores
- **Deployment**: Docker + Google Cloud Run + Cloud SQL

## Component Organization

### Frontend Structure
- **Views**: Page-level components (`views/`) - AssistantsView, ChatView, DashboardView
- **Layouts**: Layout components (`layouts/`) - DashboardLayout with navigation
- **Feature Components**: Grouped by functionality (`components/auth/`, `components/chat/`, `components/assistant/`)
- **Base Components**: Reusable UI primitives (`components/common/`) - BaseButton, BaseInput
- **Composables**: Reusable logic (`composables/`) - useWebSocket, useFileUpload, useForm

### Backend Structure
- **Main App** (`main.py`): FastAPI application with CORS, lifespan events, and router mounting
- **Database** (`models/database.py`): SQLAlchemy models and database initialization
- **Configuration** (`utils/config.py`): Environment-based settings management
- **WebSocket** (`utils/websocket.py`): Real-time communication handling

### API Modules
- **Authentication** (`api/auth.py`): User registration, login, JWT token management
- **Assistants** (`api/assistants.py`): Legacy Assistants API endpoints
- **Chat/Threads** (`api/chat.py`, `api/threads.py`): Conversation management

## Database Models
- `User`: User authentication and profiles
- `Assistant`: Both legacy and modern assistant configurations
- `Conversation`: Modern conversation sessions (replaces threads)
- `ConversationMessage`: Individual messages with token tracking

## State Management

### Pinia Stores
- **Auth Store** (`stores/auth.ts`): JWT token management with localStorage persistence
- **Assistants Store** (`stores/assistants.ts`): Assistant CRUD operations  
- **Chat Store** (`stores/chat.ts`): Chat sessions and messaging
- **Conversations Store** (`stores/conversations.ts`): Modern conversation management

## Key Components & Composables
- **Authentication**: JWT with axios interceptors in `utils/setupInterceptors.ts`
- **WebSocket**: Real-time chat using `composables/useWebSocket.ts`
- **File Upload**: Drag-and-drop with `composables/useFileUpload.ts` and `components/upload/FileUploadZone.vue`
- **API Client**: Centralized HTTP client in `utils/api.ts`
- **Form Utilities**: `composables/useForm.ts` and `composables/useDebounce.ts`
- **Image Handling**: `components/chat/ImageDisplay.vue`, `ImageGallery.vue`, and `ImageUpload.vue`

## Cost Management

The Responses API can cause exponential token growth. The system implements:
- Maximum 50 messages per conversation
- Context window optimization (last 20 messages)
- Token usage tracking per message
- Automatic conversation splitting when needed

### Built-in Tools Integration
Modern assistants support OpenAI's built-in tools:
- **Web Search**: $25-30 per 1000 queries
- **File Search**: $2.50 per 1000 queries + storage costs
- **Code Interpreter**: Standard token rates
- **Computer Use**: $3/1M input + $12/1M output tokens
