# VueMultiAgentCreator - Claude AI Assistant Instructions

## Project Overview
VueMultiAgentCreator is a Vue.js 3 frontend with FastAPI backend for managing OpenAI assistants. The application is deployed on Google Cloud Platform using Cloud Run, Cloud SQL, and Secret Manager.

## Current Deployment - UPDATED 2025-07-31
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

## Development Notes
- Frontend: Vue 3 + TypeScript + Vite + Tailwind CSS + Pinia
- Backend: FastAPI + SQLAlchemy + MySQL
- Real-time features use WebSockets
- Password validation uses onSubmit validation to avoid closure issues

## Next Steps for Implementation
1. **Backend Endpoints Needed**:
   - `/api/assistants` - CRUD operations for AI assistants
   - `/api/chat/sessions` - Managing chat sessions
   - `/api/chat/messages` - WebSocket endpoint for real-time chat
   - `/api/assistants/{id}/threads` - Managing assistant conversation threads

2. **Remove Test Endpoint**:
   - Remove `/api/auth/reset-all-users-test-only` before production

## Authentication Debug Process (RESOLVED)
The authentication issue was resolved through:
1. Adding debug logging to trace token flow
2. Discovering backend response format mismatch
3. Updating API response parsing to handle nested format
4. Fixing CORS by updating environment variables
5. Adding token validation to prevent invalid tokens