"""
FastAPI backend for Vue Multi-Agent Creator
Provides API endpoints for OpenAI assistant management
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from api import auth, assistants, threads, files, chat, dashboard, profile
from models.database import init_db
from utils.config import settings

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("Starting up...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        logger.warning("Application starting without database - some features may not work")
    yield
    # Shutdown
    logger.info("Shutting down...")

# Create FastAPI app
app = FastAPI(
    title="Vue Multi-Agent Creator API",
    description="Backend API for managing OpenAI assistants",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS - Allow both Cloud Run URL formats
allowed_origins = [settings.FRONTEND_URL]

# Also allow the project-number-based URL format (both are the same service)
if "d6mqo7ynsq-uc.a.run.app" in settings.FRONTEND_URL:
    # Add the new URL format
    allowed_origins.append("https://vue-multiagent-frontend-887330536517.us-central1.run.app")
elif "887330536517.us-central1.run.app" in settings.FRONTEND_URL:
    # Add the legacy URL format
    allowed_origins.append("https://vue-multiagent-frontend-d6mqo7ynsq-uc.a.run.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])

# Primary Assistants API (Proven and Stable)
app.include_router(assistants.router, prefix="/api/assistants", tags=["assistants"])
app.include_router(threads.router, prefix="/api/threads", tags=["threads"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(profile.router, prefix="/api", tags=["profile"])



@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Vue Multi-Agent Creator API",
        "status": "healthy",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Google Cloud Run"""
    return {"status": "healthy"}

@app.get("/test-db")
async def test_database():
    """Test database connection"""
    import os
    from models.database import engine
    from sqlalchemy import text
    try:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return {
                "status": "connected",
                "db_host": os.getenv("DB_HOST"),
                "db_user": os.getenv("DB_USER"),
                "db_pass_exists": bool(os.getenv("DB_PASS")),
                "db_pass_length": len(os.getenv("DB_PASS", "")),
                "test_query": "success"
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "db_host": os.getenv("DB_HOST"),
            "db_user": os.getenv("DB_USER"),
            "db_pass_exists": bool(os.getenv("DB_PASS")),
            "db_pass_length": len(os.getenv("DB_PASS", ""))
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )