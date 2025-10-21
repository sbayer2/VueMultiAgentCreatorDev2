# VueMultiAgentCreator - Claude Code Instructions

This file provides guidance to Claude Code when working with this repository.

## Quick Reference

**Current Deployment** (Updated 2025-08-21):
- Frontend: https://vue-multiagent-frontend-129438231958.us-central1.run.app
- Backend: https://vue-multiagent-backend-129438231958.us-central1.run.app
- Project: mythic-aloe-467602-t4
- Database: vue_app on Cloud SQL (MySQL 8.0)

## Documentation Structure

See @README.md for project overview
See @docs/architecture.md for complete system architecture
See @docs/deployment.md for deployment procedures and commands
See @docs/authentication.md for authentication flow details
See @docs/changelog.md for complete change history

## Core Development Principles

1. **File Management**:
   - NEVER create files unless absolutely necessary
   - ALWAYS prefer editing existing files
   - NEVER proactively create documentation files (*.md) unless explicitly requested

2. **Code Style**:
   - Follow existing patterns in the codebase
   - Use TypeScript for frontend, Python type hints for backend
   - Maintain consistent formatting (Prettier/ESLint for frontend, Black for backend)

## Critical Commands

### Deployment
```bash
# Full deployment (frontend + backend)
gcloud builds submit --config cloudbuild.yaml

# Quick service update
gcloud run deploy

# Check deployment logs
gcloud logging read "resource.type=cloud_run_revision" --limit=20 --project=mythic-aloe-467602-t4
```

### Development
```bash
# Frontend (from frontend/)
npm run dev              # Dev server on port 5173
npm run build            # Production build
npm run type-check       # TypeScript validation

# Backend (from backend/)
python main.py           # FastAPI server on port 8000
uvicorn main:app --reload
```

### Docker
```bash
docker-compose up        # All services (frontend:5173, backend:8000, mysql:3306, redis:6379)
docker-compose up --build
```

## Environment Variables (Backend)

Required for deployment:
- `OPENAI_API_KEY`: OpenAI API access
- `SECRET_KEY`: JWT token signing
- `DB_PASS`, `DB_HOST`, `DB_USER`, `DB_NAME`: Database connection
- `FRONTEND_URL`: CORS configuration

## Current Active Development

### Working Features ✅
- Authentication with JWT tokens (registration, login, forgot password)
- Assistant CRUD operations (create, read, update, delete)
- Chat interface with WebSocket real-time messaging
- File upload with vision/assistant file separation
- Forgot password with email delivery

### Active Focus Areas
- Cost monitoring dashboard for OpenAI built-in tools
- Migration from Assistants API to Responses API
- Performance optimization for large response handling

## Known Constraints

### OpenAI Assistants API
- Assistants API will be deprecated in mid-2026
- Current implementation uses thread-based conversations
- Each user-assistant pair maintains persistent thread

### Cost Management
- Monitor token usage in conversation_messages table
- Built-in tools have specific costs:
  - Web Search: $25-30 per 1000 queries
  - File Search: $2.50 per 1000 queries
  - Code Interpreter: Standard token rates
  - Computer Use: $3/1M input + $12/1M output tokens

## Testing & Debugging

### Quick Tests
```bash
# Test registration
curl -X POST https://vue-multiagent-backend-129438231958.us-central1.run.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@example.com","password":"Pass123","confirmPassword":"Pass123"}'

# Check service-specific logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=vue-multiagent-backend" \
  --limit=20 --project=mythic-aloe-467602-t4
```

### API Documentation
- Swagger UI: https://vue-multiagent-backend-129438231958.us-central1.run.app/docs
- Health check: GET /health
- Database test: GET /test-db

## Production Checklist

Before deploying to production:
- [ ] Remove `/api/auth/reset-all-users-test-only` endpoint
- [ ] Implement cost monitoring dashboard
- [ ] Complete Responses API migration
- [ ] Set up proper monitoring alerts
- [ ] Configure backup strategy for Cloud SQL

## Additional Notes

For detailed architectural information, deployment history, or specific implementation details, refer to the documentation files listed at the top of this file using the `@docs/filename.md` syntax.
- Option C: CLI Script (No API endpoint needed)

  # backend/scripts/reset_db.py

  import sys
  from sqlalchemy import create_engine
  from sqlalchemy.orm import sessionmaker
  from models.database import Base, User, UserAssistant, Conversation,
  etc...

  def reset_database(keep_users=False):
      """Reset database via CLI script"""

      print("⚠️  WARNING: This will delete ALL data!")
      confirm = input("Type 'RESET' to confirm: ")

      if confirm != "RESET":
          print("Aborted.")
          return

      # Delete all data...
      print("✅ Database reset complete")

  if __name__ == "__main__":
      reset_database()

  Run it:
  python backend/scripts/reset_db.py
- 2. Database Reset for Super User (Ideas for Future)

  Here are several approaches for implementing a database reset feature:

  Option A: Admin Role + Reset Endpoint (Recommended)

  # backend/api/admin.py (new file)

  @router.delete("/admin/reset-database")
  async def reset_database(
      current_user: User = Depends(get_current_admin),  # Only admins
      db: Session = Depends(get_db)
  ):
      """Reset entire database - DANGEROUS!"""

      # Delete all data in order (foreign key constraints)
      db.query(ConversationMessage).delete()
      db.query(Conversation).delete()
      db.query(FileMetadata).delete()
      db.query(UserAssistant).delete()

      # Option: Keep admin user, delete others
      db.query(User).filter(User.is_admin == False).delete()

      db.commit()
      return {"message": "Database reset successfully"}

  Database changes needed:
  # Add to User model
  is_admin: bool = Column(Boolean, default=False)