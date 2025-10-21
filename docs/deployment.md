# Deployment Guide

## Current Deployment (UPDATED 2025-08-21)

- **Project**: mythic-aloe-467602-t4
- **Frontend URL**: https://vue-multiagent-frontend-129438231958.us-central1.run.app
- **Backend URL**: https://vue-multiagent-backend-129438231958.us-central1.run.app
- **Cloud SQL Instance**: vue-multiagent-db (MySQL 8.0)
- **Database**: vue_app
- **DB User**: root

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

## Deployment Commands

### Full Deployment
```bash
gcloud builds submit --config cloudbuild.yaml
```

### Quick Service Updates
```bash
gcloud run deploy
```

### Frontend and Backend (Separate Services)
Frontend and backend are separate Cloud Run services deployed independently.

## Monitoring & Logs

### Check Logs
```bash
gcloud logging read "resource.type=cloud_run_revision" --limit=20 --project=mythic-aloe-467602-t4
```

### Service-Specific Logs
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=vue-multiagent-backend" --limit=20 --project=mythic-aloe-467602-t4
```

## Testing Commands

### Registration Test
```bash
curl -X POST https://vue-multiagent-backend-129438231958.us-central1.run.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@example.com","password":"Pass123","confirmPassword":"Pass123"}'
```

### Reset DB (Test Only - Remove Before Production)
```bash
curl -X DELETE https://vue-multiagent-backend-129438231958.us-central1.run.app/api/auth/reset-all-users-test-only
```

## Development Commands

### Frontend (from frontend/ directory)
```bash
npm run dev          # Start Vite dev server (port 5173)
npm run build        # Production build
npm run preview      # Preview production build
npm run lint         # ESLint
npm run format       # Prettier
npm run type-check   # TypeScript checking
```

### Backend (from backend/ directory)
```bash
python main.py                    # Start FastAPI server (port 8000)
uvicorn main:app --reload         # Alternative startup
python reset_db.py                # Reset database (dev only)
```

### Docker Development
```bash
docker-compose up                 # Start all services
docker-compose build              # Build containers
docker-compose up --build         # Build and start
```

Services:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs
- MySQL: localhost:3306
- Redis: localhost:6379

## Production Cleanup Tasks

Before production deployment:
- Remove `/api/auth/reset-all-users-test-only` endpoint
- Complete frontend migration from Assistants API to Responses API
- Implement cost monitoring dashboard for built-in tools usage
