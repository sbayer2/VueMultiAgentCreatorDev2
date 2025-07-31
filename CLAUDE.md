# VueMultiAgentCreator - Claude AI Assistant Instructions

## Project Overview
VueMultiAgentCreator is a Vue.js 3 frontend with FastAPI backend for managing OpenAI assistants. The application is deployed on Google Cloud Platform using Cloud Run, Cloud SQL, and Secret Manager.

## Current Deployment
- **Project**: My Project 73302 (mythic-aloe-467602-t4)
- **Frontend URL**: https://vue-multiagent-frontend-3z6nrfedzq-uc.a.run.app
- **Backend URL**: https://vue-multiagent-backend-3z6nrfedzq-uc.a.run.app
- **Cloud SQL IP**: 34.45.198.154
- **Database**: multiagent_db
- **DB User**: vueapp (using root for deployment)

## Important Instructions
1. **File Management**:
   - NEVER create files unless absolutely necessary
   - ALWAYS prefer editing existing files
   - NEVER proactively create documentation files (*.md) unless explicitly requested

2. **Deployment**:
   - Use `gcloud builds submit --config cloudbuild.yaml` for full deployment
   - Use `gcloud run deploy` for quick service updates
   - Frontend and backend are separate Cloud Run services

3. **Authentication Flow**:
   - JWT tokens stored in localStorage as 'auth_token'
   - Axios interceptors configured in setupInterceptors.ts
   - Auth state managed by Pinia store with persistence

4. **Known Issues Resolved**:
   - CORS: Fixed by setting correct FRONTEND_URL environment variable
   - Auth redirect: Fixed circular dependency in axios interceptors
   - API paths: Frontend uses /api prefix, backend serves at root

5. **Testing Commands**:
   - Registration: `curl -X POST https://vue-multiagent-backend-3z6nrfedzq-uc.a.run.app/api/auth/register -H "Content-Type: application/json" -d '{"name":"Test","email":"test@example.com","password":"Pass123","confirmPassword":"Pass123"}'`
   - Check logs: `gcloud logging read "resource.type=cloud_run_revision" --limit=20 --project=mythic-aloe-467602-t4`

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