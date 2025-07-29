"""File management endpoints"""
import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from openai import OpenAI

from models.database import get_db, User, FileMetadata
from api.auth import get_current_user
from utils.config import settings

router = APIRouter()
client = OpenAI(api_key=settings.OPENAI_API_KEY)

class FileResponse(BaseModel):
    file_id: str
    filename: str
    size: int
    purpose: str

@router.post("/upload", response_model=FileResponse)
async def upload_file(
    file: UploadFile = File(...),
    purpose: str = "assistants",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload file to OpenAI"""
    # Validate file size (25MB limit)
    contents = await file.read()
    file_size = len(contents)
    if file_size > 25 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 25MB limit"
        )
    
    # Reset file position
    await file.seek(0)
    
    try:
        # Upload to OpenAI
        openai_file = client.files.create(
            file=await file.read(),
            purpose=purpose
        )
        
        # Save metadata to database
        db_file = FileMetadata(
            file_id=openai_file.id,
            original_name=file.filename,
            size=file_size,
            mime_type=file.content_type,
            purpose=purpose,
            uploaded_by=current_user.id
        )
        db.add(db_file)
        db.commit()
        
        return FileResponse(
            file_id=openai_file.id,
            filename=file.filename,
            size=file_size,
            purpose=purpose
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to upload file: {str(e)}"
        )

@router.get("/", response_model=List[FileResponse])
async def list_files(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's uploaded files"""
    files = db.query(FileMetadata).filter(
        FileMetadata.uploaded_by == current_user.id
    ).all()
    
    return [
        FileResponse(
            file_id=f.file_id,
            filename=f.original_name,
            size=f.size,
            purpose=f.purpose
        )
        for f in files
    ]

@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete file"""
    # Check if user owns the file
    db_file = db.query(FileMetadata).filter(
        FileMetadata.file_id == file_id,
        FileMetadata.uploaded_by == current_user.id
    ).first()
    
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    try:
        # Delete from OpenAI
        client.files.delete(file_id)
        
        # Delete from database
        db.delete(db_file)
        db.commit()
        
        return {"message": "File deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete file: {str(e)}"
        )