from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import bcrypt
import re

from models.database import get_db, User
from api.auth import get_current_user

router = APIRouter()

# Pydantic models for request/response
class UserProfile(BaseModel):
    id: int
    username: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class UpdateProfileRequest(BaseModel):
    username: Optional[str] = None

    @validator('username')
    def validate_username(cls, v):
        if v is not None:
            # Username validation: alphanumeric and underscores, 3-20 chars
            if not re.match(r'^[a-zA-Z0-9_]{3,20}$', v):
                raise ValueError('Username must be 3-20 characters and contain only letters, numbers, and underscores')
        return v

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)

    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class UserStats(BaseModel):
    total_assistants: int
    total_conversations: int
    total_messages: int
    storage_used_mb: float

@router.get("/profile", response_model=UserProfile)
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user's profile information."""
    return UserProfile(
        id=current_user.id,
        username=current_user.username,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )

@router.put("/profile", response_model=UserProfile)
async def update_profile(
    request: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user profile information."""

    # Check if username is being changed and if it's already in use
    if request.username and request.username != current_user.username:
        existing_user = db.query(User).filter(User.username == request.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already in use"
            )

    # Update fields if provided
    if request.username is not None:
        current_user.username = request.username

    current_user.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(current_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )

    return UserProfile(
        id=current_user.id,
        username=current_user.username,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )

@router.post("/profile/change-password")
async def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Change user password."""

    # Verify current password
    if not bcrypt.checkpw(request.current_password.encode('utf-8'),
                         current_user.password_hash.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Hash new password
    new_password_hash = bcrypt.hashpw(
        request.new_password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

    # Update password
    current_user.password_hash = new_password_hash
    current_user.updated_at = datetime.utcnow()

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}"
        )

    return {"message": "Password changed successfully"}

@router.get("/profile/stats", response_model=UserStats)
async def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user statistics and usage information."""
    from models.database import UserAssistant, Conversation, ConversationMessage, FileMetadata

    # Count assistants
    total_assistants = db.query(UserAssistant).filter(
        UserAssistant.user_id == current_user.id
    ).count()

    # Count conversations (if using the new model)
    total_conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).count()

    # Count messages
    total_messages = 0
    if total_conversations > 0:
        conversations = db.query(Conversation).filter(
            Conversation.user_id == current_user.id
        ).all()
        conversation_ids = [c.id for c in conversations]
        total_messages = db.query(ConversationMessage).filter(
            ConversationMessage.conversation_id.in_(conversation_ids)
        ).count()

    # Calculate storage used (in MB)
    files = db.query(FileMetadata).filter(
        FileMetadata.uploaded_by == current_user.id
    ).all()
    storage_used_bytes = sum(f.size for f in files if f.size)
    storage_used_mb = round(storage_used_bytes / (1024 * 1024), 2)

    return UserStats(
        total_assistants=total_assistants,
        total_conversations=total_conversations,
        total_messages=total_messages,
        storage_used_mb=storage_used_mb
    )

@router.delete("/profile")
async def delete_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete user account and all associated data."""
    from models.database import UserAssistant, Conversation, FileMetadata

    try:
        # Delete all user's assistants
        db.query(UserAssistant).filter(UserAssistant.user_id == current_user.id).delete()

        # Delete all user's conversations
        db.query(Conversation).filter(Conversation.user_id == current_user.id).delete()

        # Delete all user's files metadata
        db.query(FileMetadata).filter(FileMetadata.uploaded_by == current_user.id).delete()

        # Delete the user
        db.delete(current_user)

        db.commit()

        return {"message": "Account deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )