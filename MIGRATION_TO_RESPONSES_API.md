# Migration to OpenAI Responses API

## Overview

This document outlines the migration from the deprecated OpenAI Assistants API to the modern Responses API, which is officially the future direction for building agents on OpenAI's platform.

## Key Migration Benefits

### 1. **Future-Proof Architecture**
- Assistants API will be deprecated in mid-2026
- Responses API is OpenAI's recommended path forward
- Access to latest models and features first

### 2. **Built-in Tools**
- **Web Search**: $25-30 per 1000 queries, powered by ChatGPT search
- **File Search**: $2.50 per 1000 queries + $0.10/GB/day storage
- **Code Interpreter**: Standard token rates
- **Computer Use**: $3/1M input + $12/1M output tokens

### 3. **Improved Performance**
- Faster response times in many cases
- Better streaming support
- More flexible conversation management

## Critical Cost Management Strategy

### ⚠️ **WARNING: Token Cost Explosion Risk**

The Responses API uses `previous_response_id` for conversation continuity, which can lead to **exponential token growth**:

- **Problem**: Each new message includes ALL previous conversation context
- **Impact**: Developers report 2.5x higher costs vs Assistants API
- **Example**: A 20-message conversation can consume 1M+ tokens per turn

### 🛡️ **Our Cost Protection Measures**

1. **Conversation Length Limits**: Max 50 messages per conversation
2. **Context Window Optimization**: Only include last 20 messages for context
3. **Token Usage Tracking**: Monitor and alert on high token consumption
4. **Smart Context Management**: Automatic conversation splitting when needed

## Database Schema Changes

### New Tables

```sql
-- Modern assistants using Responses API
CREATE TABLE assistants (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    instructions TEXT NOT NULL,
    model VARCHAR(50) DEFAULT 'gpt-4o-mini',
    tools_config TEXT,  -- JSON: built-in tools configuration
    vector_store_ids TEXT,  -- JSON: for file search
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW() ON UPDATE NOW()
);

-- Conversation sessions
CREATE TABLE conversations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT REFERENCES users(id),
    assistant_id INT REFERENCES assistants(id),
    title VARCHAR(255),
    last_response_id VARCHAR(255),  -- Critical for conversation continuity
    message_count INT DEFAULT 0,   -- Cost management
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW() ON UPDATE NOW()
);

-- Individual messages
CREATE TABLE conversation_messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    conversation_id INT REFERENCES conversations(id),
    response_id VARCHAR(255),  -- OpenAI response ID
    role VARCHAR(20) NOT NULL, -- user, assistant, system
    content TEXT NOT NULL,
    tool_calls TEXT,  -- JSON: tool usage details
    tokens_used INT,  -- Track token consumption
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Legacy Support

The old `user_assistants` table is preserved for backward compatibility during migration.

## API Endpoint Changes

### Modern Endpoints (Responses API)

```
# Assistant Management
GET    /api/assistants           # List assistants
POST   /api/assistants           # Create assistant
GET    /api/assistants/{id}      # Get assistant
PUT    /api/assistants/{id}      # Update assistant
DELETE /api/assistants/{id}      # Delete assistant

# Conversation Management
POST   /api/chat/conversations   # Create conversation
GET    /api/chat/conversations/{id}/messages  # Get messages
POST   /api/chat/conversations/{id}/messages  # Send message
DELETE /api/chat/conversations/{id}           # Delete conversation

# Streaming Chat
WebSocket: /api/chat/conversations/{id}/stream/{token}
```

### Legacy Endpoints (for migration support)

```
# Moved to /api/legacy/* namespace
GET    /api/legacy/assistants
POST   /api/legacy/assistants
# ... etc
```

## Frontend Migration

### 1. Updated TypeScript Types

```typescript
// Modern Assistant (Responses API)
interface Assistant {
  id: number
  name: string
  description?: string
  instructions: string  // replaces systemPrompt
  model: string
  tools: AssistantToolConfig  // replaces individual settings
  conversation_count: number
  created_at: string
  updated_at?: string
}

interface AssistantToolConfig {
  web_search: boolean
  file_search: boolean
  code_interpreter: boolean
  computer_use: boolean
  vector_store_ids: string[]
}

// Modern Conversation (replaces ChatSession)
interface Conversation {
  id: number
  assistant_id: number
  title?: string
  message_count: number
  created_at: string
  updated_at?: string
}
```

### 2. API Client Updates

```typescript
// Modern API calls
class ResponsesAPIClient {
  async createAssistant(data: CreateAssistantData): Promise<Assistant> {
    return this.post('/api/assistants', data)
  }
  
  async createConversation(data: CreateConversationData): Promise<Conversation> {
    return this.post('/api/chat/conversations', data)
  }
  
  async sendMessage(conversationId: number, content: string): Promise<ChatResponse> {
    return this.post(`/api/chat/conversations/${conversationId}/messages`, {
      content,
      assistant_id: this.currentAssistantId
    })
  }
}
```

### 3. WebSocket Streaming Updates

```typescript
// Modern streaming events
interface StreamMessage {
  type: 'connection' | 'text_delta' | 'complete' | 'error' | 'tool_call_created'
  // ... type-specific properties
}

// Connection to streaming endpoint
const ws = new WebSocket(
  `wss://api/chat/conversations/${conversationId}/stream/${token}`
)
```

## Built-in Tools Integration

### Web Search Example

```typescript
const assistant = await api.createAssistant({
  name: "Research Assistant",
  instructions: "You are a helpful research assistant with access to web search.",
  model: "gpt-4o",
  tools: {
    web_search: true,
    file_search: false,
    code_interpreter: false,
    computer_use: false,
    vector_store_ids: []
  }
})
```

### File Search with Vector Stores

```typescript
// First create vector store
const vectorStore = await openai.vectorStores.create({
  name: "Product Documentation",
  file_ids: [file1.id, file2.id, file3.id]
})

// Then create assistant with file search
const assistant = await api.createAssistant({
  name: "Support Assistant",
  instructions: "Answer questions using the uploaded documentation.",
  model: "gpt-4o-mini",
  tools: {
    web_search: false,
    file_search: true,
    code_interpreter: false,
    computer_use: false,
    vector_store_ids: [vectorStore.id]
  }
})
```

## Migration Checklist

### Backend Migration

- [x] Create new database models for Responses API
- [x] Implement modern assistant management endpoints
- [x] Implement conversation management with cost protection
- [x] Add WebSocket streaming for Responses API
- [x] Preserve legacy endpoints for backward compatibility
- [ ] Test all built-in tools integration
- [ ] Implement migration utility for existing data

### Frontend Migration

- [x] Update TypeScript types for Responses API
- [ ] Update assistant creation/editing components
- [ ] Update chat interface for conversation model
- [ ] Implement built-in tools UI controls
- [ ] Update WebSocket streaming handlers
- [ ] Add cost monitoring dashboard

### Testing & Deployment

- [ ] Unit tests for new API endpoints
- [ ] Integration tests with OpenAI Responses API
- [ ] Cost optimization validation
- [ ] Performance comparison tests
- [ ] Deploy to staging environment
- [ ] Production deployment with feature flags

## Deployment Strategy

### Phase 1: Parallel Implementation
1. Deploy new Responses API endpoints alongside legacy ones
2. Keep legacy endpoints functional at `/api/legacy/*`
3. Test new endpoints thoroughly

### Phase 2: Frontend Migration
1. Update frontend to use new API endpoints
2. Implement feature flags for gradual rollout
3. Monitor cost and performance metrics

### Phase 3: Legacy Deprecation
1. Migrate existing data to new schema
2. Deprecate legacy endpoints
3. Clean up old code and database tables

## Cost Monitoring Dashboard

Implement monitoring for:

- **Token Usage per Conversation**: Alert when approaching limits
- **Tool Call Costs**: Track expensive operations (web search, computer use)
- **Average Cost per Message**: Compare with legacy system
- **Conversation Length Distribution**: Identify long conversations

## Troubleshooting Common Issues

### 1. High Token Costs
- **Symptom**: Dramatically increased API costs
- **Solution**: Check conversation length limits and context window settings
- **Prevention**: Implement automatic conversation splitting

### 2. Tool Call Failures
- **Symptom**: Built-in tools not working
- **Solution**: Verify tool configuration and model compatibility
- **Example**: Computer use only works with `computer-use-preview` model

### 3. Streaming Issues
- **Symptom**: WebSocket connections failing
- **Solution**: Check token authentication and conversation ownership
- **Debug**: Monitor WebSocket connection events

## Best Practices

1. **Always Implement Cost Limits**: Never deploy without conversation length limits
2. **Monitor Token Usage**: Set up alerts for unusual consumption patterns
3. **Use Appropriate Models**: Match model to task complexity and cost requirements
4. **Test Tools Thoroughly**: Built-in tools have different pricing and capabilities
5. **Plan for Migration**: Keep legacy endpoints during transition period

## Support Resources

- **OpenAI Documentation**: https://platform.openai.com/docs/quickstart?api-mode=responses
- **Community Discussions**: Monitor OpenAI developer forums for migration tips
- **Cost Calculator**: Use OpenAI pricing calculator for cost projections

---

*This migration preserves all existing functionality while providing access to modern OpenAI capabilities with proper cost management.*