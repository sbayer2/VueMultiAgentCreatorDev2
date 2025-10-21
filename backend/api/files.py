"""File management endpoints with image upload support"""
import os
import io
import uuid
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from openai import OpenAI
from PIL import Image
import base64

from models.database import get_db, User, FileMetadata, UserAssistant
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



@router.post("/upload-for-assistant", response_model=FileResponse)
async def upload_file_for_assistant(
    file: UploadFile = File(...),
    purpose: Optional[str] = Form(None),  # Accept purpose from frontend
    assistant_id: Optional[str] = Form(None),  # Assistant to attach file to
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload file for assistant use (images and documents) - MMACTEMP pattern"""
    # Determine file types
    is_image = file.content_type in SUPPORTED_IMAGE_TYPES
    is_document = file.content_type in SUPPORTED_DOCUMENT_TYPES
    
    if not is_image and not is_document:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. Supported: images and documents"
        )
    
    # Use purpose from frontend, or determine by file type (correct MMACTEMP)
    if purpose is None or purpose == "":
        purpose = "vision" if is_image else "assistants"
    
    # Log for debugging
    print(f"DEBUG: Assistant file upload - filename: {file.filename}, purpose: {purpose}, content_type: {file.content_type}, assistant_id: {assistant_id}")
    
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

        # Upload to OpenAI Files API with correct purpose
        # Images use 'vision' (allows downloading), documents use 'assistants' (for code_interpreter)
        openai_purpose = 'vision' if is_image else 'assistants'
        openai_file = client.files.create(
            file=file_obj,
            purpose=openai_purpose
        )
        print(f"DEBUG: File uploaded to OpenAI - file_id: {openai_file.id}, filename: {openai_file.filename}")
        
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
        
        # Attach file to assistant tool_resources.code_interpreter.file_ids (CRITICAL for assistant to access files)
        if assistant_id and purpose == 'assistants':
            try:
                # Verify user owns the assistant
                db_assistant = db.query(UserAssistant).filter(
                    UserAssistant.assistant_id == assistant_id,
                    UserAssistant.user_id == current_user.id
                ).first()

                if db_assistant:
                    # Get current assistant file_ids from OpenAI
                    try:
                        print(f"DEBUG: Retrieving assistant {assistant_id} to get current file_ids")
                        openai_assistant = client.beta.assistants.retrieve(assistant_id)
                        current_openai_file_ids = []
                        if (hasattr(openai_assistant, 'tool_resources') and openai_assistant.tool_resources and
                            hasattr(openai_assistant.tool_resources, 'code_interpreter') and
                            openai_assistant.tool_resources.code_interpreter and
                            hasattr(openai_assistant.tool_resources.code_interpreter, 'file_ids')):
                            current_openai_file_ids = openai_assistant.tool_resources.code_interpreter.file_ids or []
                        print(f"DEBUG: Current assistant file_ids: {current_openai_file_ids}")
                    except Exception as e:
                        print(f"DEBUG: Failed to retrieve assistant {assistant_id}: {str(e)}")
                        # If we can't retrieve the assistant, assume no existing files
                        current_openai_file_ids = []

                    # Add new file to OpenAI assistant if not already there
                    if openai_file.id not in current_openai_file_ids:
                        updated_file_ids = current_openai_file_ids + [openai_file.id]
                        print(f"DEBUG: Updating assistant {assistant_id} tool_resources with file_ids: {updated_file_ids}")
                        try:
                            client.beta.assistants.update(
                                assistant_id=assistant_id,
                                tool_resources={"code_interpreter": {"file_ids": updated_file_ids}}
                            )
                            print(f"DEBUG: Successfully updated assistant {assistant_id} with file {openai_file.id}")
                        except Exception as e:
                            print(f"DEBUG: Failed to update assistant {assistant_id} tool_resources: {str(e)}")
                            raise

                        # Update database to track the new file
                        db_file_ids = json.loads(db_assistant.file_ids) if db_assistant.file_ids else []
                        if openai_file.id not in db_file_ids:
                            updated_db_file_ids = db_file_ids + [openai_file.id]
                            db_assistant.file_ids = json.dumps(updated_db_file_ids)
                            db.commit()

                        print(f"DEBUG: Attached file {openai_file.id} to assistant {assistant_id}")
                    else:
                        print(f"DEBUG: File {openai_file.id} already attached to assistant {assistant_id}")
                else:
                    print(f"DEBUG: Assistant {assistant_id} not found or not owned by user")

            except Exception as e:
                print(f"DEBUG: Failed to attach file to assistant: {str(e)}")
                # Don't fail the upload if assistant attachment fails
        
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

class FileDetailsRequest(BaseModel):
    file_ids: List[str]

@router.post("/details", response_model=List[FileResponse])
async def get_file_details(
    request: FileDetailsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get details for a specific list of file IDs."""
    if not request.file_ids:
        return []
    
    files = db.query(FileMetadata).filter(
        FileMetadata.file_id.in_(request.file_ids),
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
    file_id: str
):
    """Serve OpenAI file content (images from assistant responses) - MMACTEMP pattern

    Note: This endpoint is public (no auth required) because:
    - File IDs are secure random tokens from OpenAI
    - Images need to be displayable in <img> tags (which don't send auth headers)
    - No sensitive user data is exposed through file content
    """
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