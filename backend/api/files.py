"""File management endpoints with image upload support"""
import os
import io
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from openai import OpenAI
from PIL import Image
import base64

from models.database import get_db, User, FileMetadata
from api.auth import get_current_user
from utils.config import settings

router = APIRouter()
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Supported image formats
SUPPORTED_IMAGE_TYPES = {
    'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'
}

# Supported document formats (MMACTEMP pattern)
SUPPORTED_DOCUMENT_TYPES = {
    'text/plain', 'text/csv', 'application/json',
    'application/pdf', 'text/markdown', 'text/html',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/msword', 'application/vnd.ms-excel'
}

class FileResponse(BaseModel):
    file_id: str
    filename: str
    size: int
    purpose: str

class ImageAttachmentResponse(BaseModel):
    id: str
    file_id: str
    name: str
    size: int
    type: str
    url: Optional[str] = None
    preview_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    uploaded_at: str

@router.post("/upload", response_model=ImageAttachmentResponse)
async def upload_image(
    file: UploadFile = File(...),
    purpose: str = None,  # Will be determined by MMACTEMP pattern
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload image file with vision support"""
    # MMACTEMP Pattern: Determine purpose by file extension (lines 646-652)
    if purpose is None:
        file_extension = file.filename.split('.')[-1].lower() if file.filename else ''
        if file_extension in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
            purpose = 'vision'
        else:
            purpose = 'assistants'
    
    # Validate file type
    if not file.content_type or file.content_type not in SUPPORTED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Supported types: {', '.join(SUPPORTED_IMAGE_TYPES)}"
        )
    
    # Read file contents
    contents = await file.read()
    file_size = len(contents)
    
    # Validate file size (10MB limit for images)
    max_size = 10 * 1024 * 1024  # 10MB
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image size exceeds 10MB limit"
        )
    
    try:
        # Process image to get dimensions and create preview
        image_info = await process_image(contents, file.content_type)
        
        # Create temporary file-like object for OpenAI upload
        file_obj = io.BytesIO(contents)
        file_obj.name = file.filename or f"image_{uuid.uuid4().hex}.jpg"
        
        # Upload to OpenAI Files API
        openai_file = client.files.create(
            file=file_obj,
            purpose=purpose
        )
        
        # Generate unique ID for our system
        attachment_id = str(uuid.uuid4())
        
        # Save metadata to database with image-specific fields
        from datetime import datetime
        
        db_file = FileMetadata(
            file_id=openai_file.id,
            original_name=file.filename or file_obj.name,
            size=file_size,
            mime_type=file.content_type,
            purpose=purpose,
            uploaded_by=current_user.id,
            width=image_info.get('width'),
            height=image_info.get('height'),
            preview_data=image_info.get('preview_base64')
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        # Build response
        return ImageAttachmentResponse(
            id=attachment_id,
            file_id=openai_file.id,
            name=file.filename or file_obj.name,
            size=file_size,
            type=file.content_type,
            url=f"/api/files/{openai_file.id}/content",
            preview_url=f"/api/files/{openai_file.id}/preview" if image_info.get('preview_base64') else None,
            width=image_info.get('width'),
            height=image_info.get('height'),
            uploaded_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to upload image: {str(e)}"
        )

async def process_image(contents: bytes, content_type: str) -> dict:
    """Process image to extract metadata and create preview"""
    try:
        # Open image with PIL
        image = Image.open(io.BytesIO(contents))
        
        # Get dimensions
        width, height = image.size
        
        # Create thumbnail for preview (max 200x200)
        thumbnail = image.copy()
        thumbnail.thumbnail((200, 200), Image.Resampling.LANCZOS)
        
        # Convert thumbnail to base64 for storage
        thumbnail_buffer = io.BytesIO()
        thumbnail_format = 'JPEG' if content_type in ['image/jpeg', 'image/jpg'] else 'PNG'
        thumbnail.save(thumbnail_buffer, format=thumbnail_format, quality=85)
        thumbnail_base64 = base64.b64encode(thumbnail_buffer.getvalue()).decode('utf-8')
        
        return {
            'width': width,
            'height': height,
            'preview_base64': f"data:{content_type};base64,{thumbnail_base64}"
        }
        
    except Exception as e:
        print(f"Image processing error: {e}")
        return {'width': None, 'height': None, 'preview_base64': None}

@router.post("/upload-for-assistant", response_model=FileResponse)
async def upload_file_for_assistant(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload file for assistant use (images and documents) - MMACTEMP pattern"""
    # Determine purpose based on file type
    is_image = file.content_type in SUPPORTED_IMAGE_TYPES
    is_document = file.content_type in SUPPORTED_DOCUMENT_TYPES
    
    if not is_image and not is_document:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. Supported: images and documents"
        )
    
    # Set purpose for OpenAI (assistants for code_interpreter)
    purpose = "assistants"
    
    # Read file contents
    contents = await file.read()
    file_size = len(contents)
    
    # Validate file size (25MB limit like MMACTEMP)
    max_size = 25 * 1024 * 1024  # 25MB
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 25MB limit"
        )
    
    try:
        # Create file-like object for OpenAI upload
        file_obj = io.BytesIO(contents)
        file_obj.name = file.filename or f"file_{uuid.uuid4().hex}"
        
        # Upload to OpenAI Files API
        openai_file = client.files.create(
            file=file_obj,
            purpose=purpose
        )
        
        # Save metadata to database (minimal metadata for assistant files)
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
            filename=file.filename or "unknown",
            size=file_size,
            purpose=purpose
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to upload file: {str(e)}"
        )

@router.post("/upload-legacy", response_model=FileResponse)
async def upload_file_legacy(
    file: UploadFile = File(...),
    purpose: str = "assistants",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Legacy file upload endpoint"""
    # Validate file size (25MB limit)
    contents = await file.read()
    file_size = len(contents)
    if file_size > 25 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 25MB limit"
        )
    
    try:
        # Create temporary file-like object for OpenAI upload
        file_obj = io.BytesIO(contents)
        file_obj.name = file.filename or f"file_{uuid.uuid4().hex}"
        
        # Upload to OpenAI
        openai_file = client.files.create(
            file=file_obj,
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
        db.rollback()
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

@router.get("/by-purpose")
async def get_files_by_purpose(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get files organized by purpose (MMACTEMP pattern)"""
    files = db.query(FileMetadata).filter(
        FileMetadata.uploaded_by == current_user.id
    ).all()
    
    result = {
        'assistants': {},
        'vision': {}
    }
    
    for file in files:
        result[file.purpose][file.file_id] = file.original_name
    
    return result

@router.get("/{file_id}/content")
async def get_file_content(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get file content from OpenAI Files API"""
    # Check if user has access to this file
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
        # Get file content from OpenAI
        file_response = client.files.content(file_id)
        content = file_response.content
        
        # Return appropriate response based on file type
        media_type = db_file.mime_type or "application/octet-stream"
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"inline; filename={db_file.original_name}",
                "Cache-Control": "public, max-age=3600"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve file content: {str(e)}"
        )

@router.get("/{file_id}/preview")
async def get_file_preview(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get image preview/thumbnail"""
    # Check if user has access to this file
    db_file = db.query(FileMetadata).filter(
        FileMetadata.file_id == file_id,
        FileMetadata.uploaded_by == current_user.id
    ).first()
    
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    if not db_file.preview_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preview not available"
        )
    
    try:
        # Extract base64 data from data URL
        if db_file.preview_data.startswith('data:'):
            header, encoded = db_file.preview_data.split(',', 1)
            media_type = header.split(';')[0].split(':')[1]
            preview_bytes = base64.b64decode(encoded)
        else:
            preview_bytes = base64.b64decode(db_file.preview_data)
            media_type = db_file.mime_type or "image/jpeg"
        
        return Response(
            content=preview_bytes,
            media_type=media_type,
            headers={
                "Content-Disposition": f"inline; filename=preview_{db_file.original_name}",
                "Cache-Control": "public, max-age=86400"  # Cache for 24 hours
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve preview: {str(e)}"
        )

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
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete file: {str(e)}"
        )

@router.get("/openai/{file_id}")
async def get_openai_file_content(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """Serve OpenAI file content (images from assistant responses) - MMACTEMP pattern"""
    try:
        # Get file content from OpenAI
        file_response = client.files.content(file_id)
        file_content = file_response.read()
        
        # Get file metadata to determine content type
        try:
            file_info = client.files.retrieve(file_id)
            filename = getattr(file_info, 'filename', f'{file_id}.png')
            
            # Determine content type from filename
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                content_type = f"image/{filename.split('.')[-1].lower()}"
                if content_type == "image/jpg":
                    content_type = "image/jpeg"
            else:
                content_type = "application/octet-stream"
                
        except Exception:
            # Default to PNG if we can't get file info
            content_type = "image/png"
            filename = f"{file_id}.png"
        
        return Response(
            content=file_content,
            media_type=content_type,
            headers={
                "Content-Disposition": f"inline; filename={filename}",
                "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to retrieve file: {str(e)}"
        )