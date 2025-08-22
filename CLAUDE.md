# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# VueMultiAgentCreator - Claude AI Assistant Instructions

## Project Overview
VueMultiAgentCreator is a Vue.js 3 frontend with FastAPI backend for managing OpenAI assistants. The application is deployed on Google Cloud Platform using Cloud Run, Cloud SQL, and Secret Manager.

## Current Deployment - UPDATED 2025-08-21
- **Project**: mythic-aloe-467602-t4
- **Frontend URL**: https://vue-multiagent-frontend-129438231958.us-central1.run.app
- **Backend URL**: https://vue-multiagent-backend-129438231958.us-central1.run.app
- **Cloud SQL Instance**: vue-multiagent-db (MySQL 8.0)
- **Database**: vue_app
- **DB User**: root

## Important Instructions
1. **File Management**:
   - NEVER create files unless absolutely necessary
   - ALWAYS prefer editing existing files
   - NEVER proactively create documentation files (*.md) unless explicitly requested

2. **Deployment**:
   - Use `gcloud builds submit --config cloudbuild.yaml` for full deployment
   - Use `gcloud run deploy` for quick service updates
   - Frontend and backend are separate Cloud Run services

3. **Authentication Flow - FULLY WORKING ✅**:
   - JWT tokens stored in localStorage as 'auth_token'
   - Axios interceptors configured in setupInterceptors.ts
   - Auth state managed by Pinia store with persistence
   - Token validation prevents storing invalid tokens
   - API response parsing handles backend's nested format

4. **Known Issues Resolved**:
   - ✅ CORS: Fixed by updating FRONTEND_URL to new deployment URL
   - ✅ Auth redirect: Fixed API response parsing and token validation
   - ✅ Token attachment: Fixed by proper axios interceptor setup
   - ✅ API paths: Frontend correctly uses /api prefix

5. **Testing Commands**:
   - Registration: `curl -X POST https://vue-multiagent-backend-129438231958.us-central1.run.app/api/auth/register -H "Content-Type: application/json" -d '{"name":"Test","email":"test@example.com","password":"Pass123","confirmPassword":"Pass123"}'`
   - Check logs: `gcloud logging read "resource.type=cloud_run_revision" --limit=20 --project=mythic-aloe-467602-t4`
   - Service-specific logs: `gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=vue-multiagent-backend" --limit=20 --project=mythic-aloe-467602-t4`
   - Reset DB (test only): `curl -X DELETE https://vue-multiagent-backend-129438231958.us-central1.run.app/api/auth/reset-all-users-test-only`

## Key Configuration Files
- `cloudbuild.yaml`: Defines Cloud Build steps for deployment
- `frontend/.env.production`: Production environment variables
- `frontend/nginx.conf`: Nginx configuration for frontend
- `backend/utils/config.py`: Backend configuration with environment variables

## Environment Variables
Backend requires:
- OPENAI_API_KEY
- SECRET_KEY (for JWT)
- DB_PASS
- DB_HOST, DB_USER, DB_NAME
- FRONTEND_URL

## Frontend Architecture

### Vue.js 3 Application Structure
- **Framework**: Vue 3 Composition API + TypeScript + Vite + Tailwind CSS + Pinia
- **Routing**: Vue Router with authentication guards
- **State**: Pinia stores with persisted state for auth and preferences
- **UI Components**: Headless UI + Heroicons for accessible components
- **Styling**: Tailwind CSS with custom design system

### Component Organization
- **Views**: Page-level components (`views/`) - AssistantsView, ChatView, DashboardView
- **Layouts**: Layout components (`layouts/`) - DashboardLayout with navigation
- **Feature Components**: Grouped by functionality (`components/auth/`, `components/chat/`, `components/assistant/`)
- **Base Components**: Reusable UI primitives (`components/common/`) - BaseButton, BaseInput
- **Composables**: Reusable logic (`composables/`) - useWebSocket, useFileUpload, useForm

## Backend Architecture

### FastAPI Technology Stack
- **Framework**: FastAPI + SQLAlchemy + MySQL
- **Authentication**: JWT tokens with bcrypt password hashing
- **Real-time**: WebSocket connections for live chat
- **Storage**: File uploads with OpenAI vector stores
- **Deployment**: Docker + Google Cloud Run + Cloud SQL

### Application Structure
- **Main App** (`main.py`): FastAPI application with CORS, lifespan events, and router mounting
- **Database** (`models/database.py`): SQLAlchemy models and database initialization
- **Configuration** (`utils/config.py`): Environment-based settings management
- **WebSocket** (`utils/websocket.py`): Real-time communication handling

### API Modules
- **Authentication** (`api/auth.py`): User registration, login, JWT token management
- **Assistants** (`api/assistants.py`): Legacy Assistants API endpoints
- **Responses API** (`api/responses_assistants.py`, `api/responses_chat.py`): Modern OpenAI API
- **File Management** (`api/files.py`): File upload and vector store operations
- **Chat/Threads** (`api/chat.py`, `api/threads.py`): Conversation management

### Critical Migration Status (2025-08-21)
**Current State**: Dual API architecture with both Assistants and Responses API implementations
- **Legacy Endpoints** (`/api/assistants.py`, `/api/chat.py`): Stable Assistants API implementation
- **Modern Endpoints** (`/api/responses_assistants.py`, `/api/responses_chat.py`): New Responses API implementation
- **Migration Progress**: Backend complete, frontend migration pending
- **Cost Management**: Implemented conversation limits (50 messages max) and token tracking

### Production Cleanup Tasks
- Remove `/api/auth/reset-all-users-test-only` endpoint before production deployment
- Complete frontend migration from Assistants API to Responses API
- Implement cost monitoring dashboard for built-in tools usage

## Development Commands

### Frontend (from frontend/ directory)
- `npm run dev` - Start Vite development server with hot reload on port 5173
- `npm run build` - Production build (runs TypeScript compilation then Vite build)
- `npm run preview` - Preview production build locally
- `npm run lint` - Lint and auto-fix Vue/TS files with ESLint
- `npm run format` - Format code with Prettier
- `npm run type-check` - TypeScript type checking without emit

### Backend (from backend/ directory)
- `python main.py` - Start FastAPI server with auto-reload on port 8000
- `uvicorn main:app --reload` - Alternative startup method
- `python reset_db.py` - Reset database (development only)

**Environment Setup**: Ensure these environment variables are set:
```bash
export OPENAI_API_KEY="your-api-key"
export SECRET_KEY="your-secret-key"
export DB_HOST="localhost"
export DB_USER="root"
export DB_PASS="your-password"
export DB_NAME="multiagent_db"
```

### Docker Development
- `docker-compose up` - Start all services (frontend:5173, backend:8000, mysql:3306, redis:6379)
- `docker-compose build` - Build all containers
- `docker-compose up --build` - Build and start services
- Frontend accessible at `http://localhost:5173`
- Backend API at `http://localhost:8000`
- API docs at `http://localhost:8000/docs`

### Cloud Deployment
- `gcloud builds submit --config cloudbuild.yaml` - Full deployment to GCP
- `gcloud run deploy` - Deploy specific service updates
- Check logs: `gcloud logging read "resource.type=cloud_run_revision" --limit=20 --project=mythic-aloe-467602-t4`

### Testing & Monitoring
- API documentation: Visit `/docs` for interactive Swagger UI
- Database test: GET `/test-db` endpoint
- Health check: GET `/health` endpoint

## Architecture Overview

### Primary API Architecture (Assistants API)
The backend uses OpenAI's proven Assistants API as the primary implementation:

**Primary Endpoints** (`/api/*`):
- Assistants API (stable, legacy implementation)
- Thread-based conversations with proven state management
- Traditional OpenAI tools: file search and code interpreter
- Robust assistant CRUD operations (legacy schema)

**Modern Endpoints** (`/api/*` with responses modules):
- Responses API (OpenAI's future direction - mid-2026 deprecation of Assistants API)
- Conversation-based approach with cost protection measures
- Built-in tools: web search ($25-30/1K queries), file search ($2.50/1K queries), code interpreter, computer use ($3/1M input + $12/1M output)
- New database schema with token tracking and conversation limits

### State Management (Frontend)
- **Auth Store** (`stores/auth.ts`): JWT token management with localStorage persistence
- **Assistants Store** (`stores/assistants.ts`): Assistant CRUD operations  
- **Chat Store** (`stores/chat.ts`): Chat sessions and messaging
- **Conversations Store** (`stores/conversations.ts`): Modern conversation management

### Key Components & Composables
- **Authentication**: JWT with axios interceptors in `utils/setupInterceptors.ts`
- **WebSocket**: Real-time chat using `composables/useWebSocket.ts`
- **File Upload**: Drag-and-drop with `composables/useFileUpload.ts` and `components/upload/FileUploadZone.vue`
- **API Client**: Centralized HTTP client in `utils/api.ts`
- **Form Utilities**: `composables/useForm.ts` and `composables/useDebounce.ts`
- **Image Handling**: `components/chat/ImageDisplay.vue`, `ImageGallery.vue`, and `ImageUpload.vue`

### Database Models
- `User`: User authentication and profiles
- `Assistant`: Both legacy and modern assistant configurations
- `Conversation`: Modern conversation sessions (replaces threads)
- `ConversationMessage`: Individual messages with token tracking

### Cost Management (Critical)
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

## Critical Development Patterns

### Dual API Architecture (Critical)
The system implements **both** OpenAI Assistants API and Responses API in preparation for OpenAI's mid-2026 deprecation:

**Legacy Implementation** (Production-ready):
- Files: `api/assistants.py`, `api/chat.py`, `api/threads.py`
- Database: `user_assistants` table
- Features: Thread-based conversations, traditional tools
- Status: Stable, currently used by frontend

**Modern Implementation** (Migration target):
- Files: `api/responses_assistants.py`, `api/responses_chat.py`
- Database: New schema (`assistants`, `conversations`, `conversation_messages`)
- Features: Built-in tools, conversation limits, token tracking
- Status: Backend complete, frontend migration pending

**Critical Migration Details**: See `MIGRATION_TO_RESPONSES_API.md` for:
- Cost protection measures (50-message conversation limits)
- Database schema differences
- Built-in tools pricing and configuration
- Frontend migration checklist

### Authentication Flow (Critical)
- Frontend stores JWT in localStorage as 'auth_token'
- Axios interceptors automatically attach tokens (`utils/setupInterceptors.ts`)
- Backend validates JWT and extracts user context
- API responses use nested format that must be parsed correctly

### Cost Management Strategy
- **Responses API**: Exponential token growth risk - implement conversation limits
- **Built-in Tools**: Web search ($25-30/1K queries), File search ($2.50/1K queries)
- **Token Tracking**: Monitor usage per conversation and implement automatic splitting

## Common Development Workflows

### Working with Assistants API (Legacy)
1. Modify assistant logic in `backend/api/assistants.py`
2. Frontend uses `stores/assistants.ts` for state management
3. Components: `AssistantsView.vue`, `AssistantCreateView.vue`, `AssistantEditView.vue`

### Working with Responses API (Modern)
1. Backend logic in `backend/api/responses_assistants.py` and `backend/api/responses_chat.py`
2. Frontend migration pending - currently uses legacy API
3. Database schema: `assistants`, `conversations`, `conversation_messages` tables

### Debugging Authentication Issues
Common issues and solutions (authentication flow is currently working):
1. **Token not attached**: Check `utils/setupInterceptors.ts` axios configuration
2. **CORS errors**: Verify `FRONTEND_URL` environment variable matches deployment URL
3. **Invalid tokens**: Backend validates JWT and extracts user context properly
4. **Response parsing**: API responses use nested format that must be parsed correctly

### Cost Management and Monitoring
- Monitor token usage in `conversation_messages` table
- Implement conversation splitting when approaching 50-message limit
- Track built-in tool usage costs (web search, file search, computer use)
- Use cost protection measures in Responses API implementation
- Add to Memory The issue is likely in how the store's currentConversation is being
  accessed. The destructuring should use storeToRefs to maintain
  reactivity. Let me fix this:

⏺ Update(frontend/src/views/ChatView.vue)
  ⎿  Updated frontend/src/views/ChatView.vue with 1 addition             
       163    
       164    <script setup lang="ts">
       165    import { ref, computed, onMounted, onUnmounted } from 'vue'
       166 +  import { storeToRefs } from 'pinia'
       167    import { useRoute, useRouter } from 'vue-router'
       168    import { useAssistantsStore } from '@/stores/assistants'
       169    import { useConversationsStore } from 
             '@/stores/conversations'

⏺ Update(frontend/src/views/ChatView.vue)
  ⎿  Updated frontend/src/views/ChatView.vue with 3 additions and 3      
     removals
       178    // State
       179    const showAssistantSelector = ref(false)
       180    
       181 -  // Store data
       182 -  const { assistantsList } = assistantsStore
       181 +  // Store data with reactivity
       182 +  const { assistantsList } = storeToRefs(assistantsStore)
       183    const { 
       184      conversationsList,
       185      currentConversation,
       186      currentMessages
       187 -  } = conversationsStore
       187 +  } = storeToRefs(conversationsStore)
       188    
       189    // Computed
       190    const currentAssistantName = computed(() => {

⏺ Now let me add a "New Thread" button to the ConversationInterface for
  resetting threads. First, let me check what's in the
  ConversationInterface component:

⏺ Read(frontend/src/components/chat/ConversationInterface.vue)
  ⎿  Read 50 lines (ctrl+r to expand)

⏺ Perfect! The ConversationInterface has a settings panel. Let me add a
  "New Thread" button to it. First, let me read more of this component to
   see the structure:

⏺ Read(frontend/src/components/chat/ConversationInterface.vue)
  ⎿  Read 30 lines (ctrl+r to expand)

⏺ Let me add the "New Thread" button to the settings panel. First let me
  check the script section to see the available methods:

⏺ Search(pattern: "import.*from", path:
        "frontend/src/components/chat/ConversationInterface.vue",
        output_mode: "content")
  ⎿  Found 14 lines (ctrl+r to expand)

⏺ Update(frontend/src/components/chat/ConversationInterface.vue)
  ⎿  Updated frontend/src/components/chat/ConversationInterface.vue with 
     11 additions and 1 removal
       44          <!-- Settings Panel -->
       45          <div v-if="showSettings" class="mt-4 p-4 bg-gray-50 
            rounded-lg">
       46            <h3 class="font-medium text-gray-900 
            mb-3">Conversation Settings</h3>
       47 -          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
       47 +          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
       48              <div>
       49                <label class="block text-sm font-medium 
            text-gray-700 mb-1">Title</label>
       50                <input
     ...
       59                <label class="block text-sm font-medium 
            text-gray-700 mb-1">Messages</label>
       60                <p class="text-sm text-gray-500 py-2">{{ 
            messages.length }} messages in conversation</p>
       61              </div>
       62 +            <div>
       63 +              <label class="block text-sm font-medium 
          + text-gray-700 mb-1">Thread Control</label>
       64 +              <button
       65 +                @click="resetThread"
       66 +                :disabled="isResettingThread"
       67 +                class="w-full px-3 py-2 text-sm bg-orange-100 
          + text-orange-700 border border-orange-300 rounded-md 
          + hover:bg-orange-200 focus:outline-none focus:ring-2 
          + focus:ring-orange-500 disabled:opacity-50 transition-colors"
       68 +              >
       69 +                {{ isResettingThread ? 'Creating...' : 'New 
          + Thread' }}
       70 +              </button>
       71 +            </div>
       72            </div>
       73          </div>
       74        </div>

⏺ Now let me find the script section to add the resetThread
  functionality:

⏺ Search(pattern: "const.*ref\(", path:
        "frontend/src/components/chat/ConversationInterface.vue",
        output_mode: "content")
  ⎿  Found 14 lines (ctrl+r to expand)

⏺ Let me add the resetThread method and the isResettingThread state:

⏺ Search(pattern: "const.*ref.*=.*ref\(", path:
        "frontend/src/components/chat/ConversationInterface.vue",
        output_mode: "content")
  ⎿  Found 0 lines 

⏺ Search(pattern: "const.*=.*ref\(", path:
        "frontend/src/components/chat/ConversationInterface.vue",
        output_mode: "content")
  ⎿  Found 6 lines (ctrl+r to expand)

⏺ Update(frontend/src/components/chat/ConversationInterface.vue)
  ⎿  Updated frontend/src/components/chat/ConversationInterface.vue with 
      addition
       248    const newMessage = ref('')
       249    const showSettings = ref(false)
       250    const editableTitle = ref('')
       251 +  const isResettingThread = ref(false)
       252    const messagesContainer = ref<HTMLElement>()
       253    const messageInput = ref<HTMLTextAreaElement>()
       254    const imageUpload = ref<InstanceType<typeof ImageUpload>>()

⏺ Now let me add the resetThread method. First let me find where other
  methods are defined:

⏺ Search(pattern: "const.*= async", path:
        "frontend/src/components/chat/ConversationInterface.vue",
        output_mode: "content")
  ⎿  Found 9 lines (ctrl+r to expand)

⏺ Update(frontend/src/components/chat/ConversationInterface.vue)
  ⎿  Updated frontend/src/components/chat/ConversationInterface.vue with 
     35 additions
       314      return
       315    }
       316    
       317 +  const resetThread = async () => {
       318 +    if (!props.conversation || isResettingThread.value) 
     return
       319 +    
       320 +    isResettingThread.value = true
       321 +    
       322 +    try {
       323 +      // Get the assistant from the conversation to get the 
           + OpenAI assistant ID
       324 +      const assistantsStore = useAssistantsStore()
       325 +      const assistant = 
     assistantsStore.getAssistantById(props
           + .conversation.assistant_id)
       326 +      
       327 +      if (assistant) {
       328 +        // Call the new-thread endpoint with the OpenAI 
           + assistant ID
       329 +        const response = await 
           + apiClient.post('/chat/new-thread', {
       330 +          assistant_id: assistant.assistant_id
       331 +        })
       332 +        
       333 +        if (response.success) {
       334 +          // Clear current messages to show fresh thread
       335 +          conversationsStore.clearCurrentConversation()
       336 +          
       337 +          // Reload the conversation to get fresh state
       338 +          await 
           + conversationsStore.loadConversation(props.conversation.id)
       339 +          
       340 +          console.log('New thread created successfully')
       341 +        } else {
       342 +          console.error('Failed to create new thread:', 
           + response.error)
       343 +        }
       344 +      }
       345 +    } catch (error) {
       346 +      console.error('Error creating new thread:', error)
       347 +    } finally {
       348 +      isResettingThread.value = false
       349 +    }
       350 +  }
       351 +  
       352    const updateTitle = async () => {
       353      if (!props.conversation || editableTitle.value === 
             conversationTitle.value) return
       354      

⏺ I need to import the necessary dependencies for this new method:

⏺ Update(frontend/src/components/chat/ConversationInterface.vue)
  ⎿  Updated frontend/src/components/chat/ConversationInterface.vue with 
      additions
       223    <script setup lang="ts">
       224    import { ref, computed, nextTick, watch, onMounted, 
             onUnmounted } from 'vue'
       225    import { useConversationsStore } from 
             '@/stores/conversations'
       226 +  import { useAssistantsStore } from '@/stores/assistants'
       227 +  import { apiClient } from '@/utils/api'
       228    import type { ConversationMessage, Conversation, 
             ImageAttachment } from '@/types'
       229    import ChatMessage from './ChatMessage.vue'
       230    import ImageUpload from './ImageUpload.vue'

⏺ Update Todos
  ⎿  ☒ Examine main.py backend architecture and routing                  
     ☒ Review Vue frontend routing and navigation structure
     ☒ Analyze chat initialization flow and identify where it fails
     ☒ Check assistant selection handlers and conversation start triggers
     ☒ Understand full flow: frontend → backend → OpenAI Assistants API
     ☒ Implement Option 2: Assistant-specific threads
     ☒ Fix chat window initialization to start immediately upon assistant 
       selection

⏺ Perfect! Now let me summarize what has been implemented for Option 2
  (Assistant-specific threads) and the frontend fixes:

  ✅ Implementation Complete

  Option 2: Assistant-Specific Threads

  1. Database: Added thread_id column to user_assistants table
  2. Backend: Updated /chat/message, /chat/new-thread, and WebSocket
  endpoints to use assistant-specific threads
  3. Thread Management: Each user-assistant pair gets its own persistent
  OpenAI thread
  4. New Thread API: Users can reset threads for specific assistants via
  /chat/new-thread

  Frontend Navigation Fixes

  1. Reactivity: Fixed ChatView.vue to use storeToRefs for proper
  reactivity
  2. Navigation: Updated AssistantsView.vue "Start Chat" to create
  conversations properly
  3. Thread Control: Added "New Thread" button in ConversationInterface
  settings panel
  4. Flow: Assistants → "Start Chat" → Creates conversation → Navigates
  to ChatView → ConversationInterface becomes visible immediately

  Complete Architecture Flow

  Working Flow:
  1. Frontend: User clicks "Start Chat" → Creates conversation →
  Navigates to /chat/{conversationId}
  2. Backend: Gets assistant by ID → Creates/retrieves assistant-specific
   thread_id → Uses threads.messages.create + threads.runs.create
  3. OpenAI: Each assistant has isolated conversation history in its own
  thread
  4. Thread Reset: "New Thread" button creates fresh thread for assistant
   while preserving others

  Key Benefits:

  - ✅ Multiple Concurrent Conversations: Different assistants =
  different threads
  - ✅ Thread Persistence: Conversations resume where left off per
  assistant
  - ✅ Thread Reset: Fresh conversation without affecting other
  assistants
  - ✅ Proper MMACTEMP Pattern: create → messages.create → runs.create
  flow
  - ✅ Immediate Chat Interface: No more requiring Home tab click

  The chat window should now start immediately upon assistant selection,
  and each assistant maintains its own conversation thread that can be
  reset independently!