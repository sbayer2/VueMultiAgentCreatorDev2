"""Thread management endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from openai import OpenAI

from models.database import get_db, User
from api.auth import get_current_user
from utils.config import settings

router = APIRouter()
client = OpenAI(api_key=settings.OPENAI_API_KEY)

class ThreadResponse(BaseModel):
    thread_id: str

@router.post("/", response_model=ThreadResponse)
async def create_thread(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new thread"""
    try:
        # Create OpenAI thread
        thread = client.beta.threads.create()
        
        # Update user's thread ID
        current_user.thread_id = thread.id
        db.commit()
        
        return ThreadResponse(thread_id=thread.id)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create thread: {str(e)}"
        )

@router.get("/current", response_model=ThreadResponse)
async def get_current_thread(
    current_user: User = Depends(get_current_user)
):
    """Get current thread"""
    if not current_user.thread_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active thread found"
        )
    
    return ThreadResponse(thread_id=current_user.thread_id)

@router.delete("/current")
async def delete_current_thread(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete current thread and create new one"""
    if current_user.thread_id:
        try:
            # Delete old thread from OpenAI
            client.beta.threads.delete(current_user.thread_id)
        except:
            pass  # Thread might already be deleted
    
    try:
        # Create new thread
        thread = client.beta.threads.create()
        current_user.thread_id = thread.id
        db.commit()
        
        return ThreadResponse(thread_id=thread.id)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create new thread: {str(e)}"
        )