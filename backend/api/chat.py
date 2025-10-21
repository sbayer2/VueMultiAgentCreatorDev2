"Chat endpoints for non-streaming HTTP communication"
import json
import asyncio
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from openai import OpenAI

from models.database import get_db, User, UserAssistant, FileMetadata
from api.auth import get_current_user
from utils.config import settings

router = APIRouter()
client = OpenAI(api_key=settings.OPENAI_API_KEY)

class ChatMessage(BaseModel):
    content: str
    assistant_id: str
    file_ids: Optional[List[str]] = None

class ImageAttachment(BaseModel):
    file_id: str
    type: str = "image"

class ChatResponse(BaseModel):
    message_id: str
    content: str
    attachments: Optional[List[ImageAttachment]] = None

@router.post("/message")
async def send_message(
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send message to assistant (non-streaming) - MMACTEMP Pattern"""
    db_assistant = db.query(UserAssistant).filter(
        UserAssistant.assistant_id == message.assistant_id,
        UserAssistant.user_id == current_user.id
    ).first()
    
    if not db_assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistant not found"
        )
    
    thread_id = db_assistant.thread_id
    if not thread_id:
        try:
            thread = client.beta.threads.create()
            thread_id = thread.id
            db_assistant.thread_id = thread_id
            db.commit()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create thread: {str(e)}"
            )
    
    try:
        # Correctly initialize lists
        message_content = [{"type": "text", "text": message.content}]
        image_file_ids = []
        file_ids_for_code_interpreter = []
        
        all_assistant_file_ids = json.loads(db_assistant.file_ids) if db_assistant.file_ids else []
        combined_file_ids = list(set(all_assistant_file_ids + (message.file_ids or [])))

        # Track new assistant files that need to be attached to the OpenAI assistant
        new_assistant_files = []
        if message.file_ids:
            for file_id in message.file_ids:
                if file_id not in all_assistant_file_ids:
                    new_assistant_files.append(file_id)

        if combined_file_ids:
            db_files = db.query(FileMetadata).filter(
                FileMetadata.file_id.in_(combined_file_ids),
                FileMetadata.uploaded_by == current_user.id
            ).all()
            for f in db_files:
                is_image = (f.mime_type and f.mime_type.startswith('image/')) or f.purpose == 'vision'
                if is_image:
                    if f.file_id not in image_file_ids:
                         image_file_ids.append(f.file_id)
                elif f.purpose == 'assistants':

                    if f.file_id not in file_ids_for_code_interpreter:
                        file_ids_for_code_interpreter.append(f.file_id)
        
        # Update OpenAI assistant with new files (attach to code_interpreter tool_resources)
        if new_assistant_files:
            new_assistant_db_files = db.query(FileMetadata).filter(
                FileMetadata.file_id.in_(new_assistant_files),
                FileMetadata.uploaded_by == current_user.id,
                FileMetadata.purpose == 'assistants'
            ).all()
            
            if new_assistant_db_files:
                try:
                    # Get current assistant file_ids from OpenAI
                    openai_assistant = client.beta.assistants.retrieve(message.assistant_id)
                    current_openai_file_ids = []
                    if (hasattr(openai_assistant, 'tool_resources') and openai_assistant.tool_resources and 
                        hasattr(openai_assistant.tool_resources, 'code_interpreter') and 
                        openai_assistant.tool_resources.code_interpreter and
                        hasattr(openai_assistant.tool_resources.code_interpreter, 'file_ids')):
                        current_openai_file_ids = openai_assistant.tool_resources.code_interpreter.file_ids or []
                    
                    # Add new assistant files to OpenAI assistant
                    assistant_file_ids_to_add = [f.file_id for f in new_assistant_db_files 
                                               if f.file_id not in current_openai_file_ids]
                    
                    if assistant_file_ids_to_add:
                        updated_file_ids = list(set(current_openai_file_ids + assistant_file_ids_to_add))
                        client.beta.assistants.update(
                            assistant_id=message.assistant_id,
                            tool_resources={"code_interpreter": {"file_ids": updated_file_ids}}
                        )
                        print(f"DEBUG: Added {len(assistant_file_ids_to_add)} new files to assistant {message.assistant_id}")
                        
                        # Update database to track the new files
                        updated_all_file_ids = list(set(all_assistant_file_ids + [f.file_id for f in new_assistant_db_files]))
                        db_assistant.file_ids = json.dumps(updated_all_file_ids)
                        db.commit()
                        
                except Exception as e:
                    print(f"DEBUG: Failed to update assistant with new files: {str(e)}")
                    # Continue with the chat even if file attachment fails
        
        for image_file_id in image_file_ids:
            if message.file_ids and image_file_id in message.file_ids:
                message_content.append({"type": "image_file", "image_file": {"file_id": image_file_id}})
        
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message_content
        )
        
        # Note: tool_resources parameter is not supported in current OpenAI client
        # Code interpreter files are managed at the assistant level, not run level
        print(f"DEBUG: Creating run for thread {thread_id} with assistant {message.assistant_id}")
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=message.assistant_id
        )
        print(f"DEBUG: Run created successfully: {run.id}")
        
        while True:
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
            if run.status in ("completed", "failed", "cancelled", "expired"):
                break
            await asyncio.sleep(0.5)
        
        if run.status == "completed":
            # Retrieve more messages to handle multi-part responses
            messages = client.beta.threads.messages.list(thread_id=thread_id, limit=20)
            
            # Find the assistant's response messages after the user's message
            assistant_messages = []
            for msg in messages.data:
                if msg.role == 'assistant':
                    assistant_messages.append(msg)
                    # Stop at the first assistant message for this run
                    if len(assistant_messages) == 1:
                        break
            
            if assistant_messages:
                # Aggregate all content from the assistant's response
                all_content_parts = []
                all_image_attachments = []
                total_chars = 0
                
                for assistant_msg in assistant_messages:
                    for content in assistant_msg.content:
                        if content.type == 'text':
                            text_value = content.text.value
                            all_content_parts.append(text_value)
                            total_chars += len(text_value)
                        elif content.type == 'image_file':
                            all_image_attachments.append(ImageAttachment(
                                file_id=content.image_file.file_id,
                                type="image"
                            ))
                
                # Log response size for monitoring
                aggregated_content = '\n'.join(all_content_parts)
                print(f"DEBUG: Response size - Messages: {len(assistant_messages)}, "
                      f"Parts: {len(all_content_parts)}, "
                      f"Total chars: {total_chars}, "
                      f"Images: {len(all_image_attachments)}")
                
                # Log if response is particularly large
                if total_chars > 10000:
                    print(f"INFO: Large response generated - {total_chars} characters for thread {thread_id}")
                
                return {
                    "success": True,
                    "data": ChatResponse(
                        message_id=assistant_messages[0].id,
                        content=aggregated_content,
                        attachments=all_image_attachments or None
                    ).dict()
                }
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Run failed with status: {run.status}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to send message: {str(e)}"
        )

class NewThreadRequest(BaseModel):
    assistant_id: str

@router.get("/messages/{assistant_id}")
async def get_thread_messages(
    assistant_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch message history for an assistant's thread."""
    db_assistant = db.query(UserAssistant).filter(
        UserAssistant.assistant_id == assistant_id,
        UserAssistant.user_id == current_user.id
    ).first()

    if not db_assistant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found")

    # If no thread exists yet, return empty messages
    if not db_assistant.thread_id:
        return {
            "success": True,
            "data": {
                "thread_id": None,
                "messages": []
            }
        }

    try:
        # Fetch messages from OpenAI thread
        messages = client.beta.threads.messages.list(
            thread_id=db_assistant.thread_id,
            limit=50,  # Fetch last 50 messages
            order="asc"  # Oldest first for chronological display
        )

        # Format messages for frontend
        formatted_messages = []
        for msg in messages.data:
            message_content = ""
            image_attachments = []

            # Extract text and image content
            for content in msg.content:
                if content.type == 'text':
                    message_content += content.text.value
                elif content.type == 'image_file':
                    image_attachments.append({
                        "file_id": content.image_file.file_id,
                        "type": "image"
                    })

            # Convert Unix timestamp to ISO string for frontend
            from datetime import datetime
            created_at_iso = datetime.fromtimestamp(msg.created_at).isoformat()

            formatted_messages.append({
                "id": msg.id,
                "role": msg.role,
                "content": message_content,
                "created_at": created_at_iso,
                "attachments": image_attachments if image_attachments else None
            })

        return {
            "success": True,
            "data": {
                "thread_id": db_assistant.thread_id,
                "messages": formatted_messages
            }
        }
    except Exception as e:
        print(f"DEBUG: Failed to fetch thread messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch messages: {str(e)}"
        )

@router.post("/new-thread")
async def create_new_thread(
    request: NewThreadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new thread for a specific assistant."""
    db_assistant = db.query(UserAssistant).filter(
        UserAssistant.assistant_id == request.assistant_id,
        UserAssistant.user_id == current_user.id
    ).first()

    if not db_assistant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found")

    try:
        thread = client.beta.threads.create()
        db_assistant.thread_id = thread.id
        db.commit()

        return {
            "success": True,
            "thread_id": thread.id,
            "assistant_id": request.assistant_id,
            "message": "New thread created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to create new thread: {str(e)}")
