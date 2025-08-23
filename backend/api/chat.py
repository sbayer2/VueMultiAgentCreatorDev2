"""Chat endpoints with WebSocket support"""
import json
import asyncio
import time
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from pydantic import BaseModel
from openai import OpenAI
from openai.types.beta.threads import Message

from models.database import get_db, User, UserAssistant, FileMetadata
from api.auth import get_current_user
from utils.config import settings
from utils.websocket import ConnectionManager

router = APIRouter()
client = OpenAI(api_key=settings.OPENAI_API_KEY)
manager = ConnectionManager()

class ChatMessage(BaseModel):
    content: str
    assistant_id: str
    file_ids: Optional[List[str]] = None

class ImageAttachment(BaseModel):
    file_id: str
    type: str = "image"
    url: Optional[str] = None
    preview_url: Optional[str] = None
    name: Optional[str] = None
    size: Optional[int] = None
    uploaded_at: Optional[str] = None

class ChatResponse(BaseModel):
    message_id: str
    content: str
    attachments: Optional[List[ImageAttachment]] = None

# Event handler for streaming with image detection (MMACTEMP pattern)
class StreamingEventHandler:
    def __init__(self, websocket: WebSocket, thread_id: str):
        self.websocket = websocket
        self.full_response = ""
        self.thread_id = thread_id
    
    async def on_text_created(self, text):
        await self.websocket.send_json({
            "type": "text_created",
            "content": text if isinstance(text, str) else text.value
        })
    
    async def on_text_delta(self, delta, snapshot):
        self.full_response += delta.value
        await self.websocket.send_json({
            "type": "text_delta",
            "content": delta.value
        })
    
    async def on_tool_call_created(self, tool_call):
        await self.websocket.send_json({
            "type": "tool_call_created",
            "tool": tool_call.type
        })
    
    async def on_tool_call_delta(self, delta, snapshot):
        if hasattr(delta, 'code_interpreter') and delta.code_interpreter:
            if hasattr(delta.code_interpreter, 'input'):
                await self.websocket.send_json({
                    "type": "code_input",
                    "content": delta.code_interpreter.input
                })
            if hasattr(delta.code_interpreter, 'outputs'):
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        await self.websocket.send_json({
                            "type": "code_output",
                            "content": output.logs
                        })
    
    async def check_for_image_outputs(self):
        """Check for image outputs in thread messages (MMACTEMP pattern)"""
        try:
            messages = client.beta.threads.messages.list(thread_id=self.thread_id)
            image_files = []
            
            for message in messages.data:
                for content in message.content:
                    if hasattr(content, 'type') and content.type == 'image_file':
                        file_id = content.image_file.file_id
                        image_files.append({
                            "file_id": file_id,
                            "type": "image_file"
                        })
            
            if image_files:
                await self.websocket.send_json({
                    "type": "image_output",
                    "images": image_files
                })
                
        except Exception as e:
            print(f"Error checking for image outputs: {e}")
            # Don't fail the whole stream for image check errors

@router.post("/message", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send message to assistant (non-streaming) - MMACTEMP Pattern"""
    print(f"DEBUG: Chat message received - assistant_id: {message.assistant_id}, content length: {len(message.content)}, file_ids: {message.file_ids}")
    print(f"DEBUG: User: {current_user.id} ({current_user.username})")
    # Get assistant-specific thread ID
    print(f"DEBUG: Looking for assistant {message.assistant_id} for user {current_user.id}")
    db_assistant = db.query(UserAssistant).filter(
        UserAssistant.assistant_id == message.assistant_id,
        UserAssistant.user_id == current_user.id
    ).first()
    
    print(f"DEBUG: Found assistant: {db_assistant is not None}")
    if db_assistant:
        print(f"DEBUG: Assistant details - name: {db_assistant.name}, thread_id: {db_assistant.thread_id}")
    
    if not db_assistant:
        print(f"DEBUG: Assistant not found - looking for assistant_id: {message.assistant_id}, user_id: {current_user.id}")
        # Let's also check what assistants exist for this user
        all_assistants = db.query(UserAssistant).filter(UserAssistant.user_id == current_user.id).all()
        print(f"DEBUG: User has {len(all_assistants)} assistants: {[a.assistant_id for a in all_assistants]}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistant not found"
        )
    
    # Create assistant-specific thread if it doesn't exist
    thread_id = db_assistant.thread_id
    if not thread_id:
        print(f"DEBUG: Creating new thread for assistant {db_assistant.name}")
        try:
            thread = client.beta.threads.create()
            thread_id = thread.id
            print(f"DEBUG: Created thread {thread_id}")
            
            # Update database with new thread ID
            db_assistant.thread_id = thread_id
            db.add(db_assistant)
            db.commit()
            print(f"DEBUG: Updated database with thread_id {thread_id}")
        except Exception as e:
            print(f"DEBUG: Error creating thread: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create thread: {str(e)}"
            )
    else:
        print(f"DEBUG: Using existing thread {thread_id}")
    
    try:
        # MMACTEMP Pattern: Separate vision files from assistant files
        message_content = [{"type": "text", "text": message.content}]
        image_file_ids = []  # Vision files for message content
        file_ids_for_code_interpreter = []  # Assistant files for tool resources
        
        # Categorize files by purpose (MMACTEMP lines 500-514)
        if message.file_ids:
            for file_id in message.file_ids:
                # Query database to check file purpose
                file_metadata = db.query(FileMetadata).filter(
                    FileMetadata.file_id == file_id,
                    FileMetadata.uploaded_by == current_user.id
                ).first()
                
                if file_metadata:
                    # Check if it's an image by MIME type or purpose
                    is_image = (file_metadata.mime_type and file_metadata.mime_type.startswith('image/')) or file_metadata.purpose == 'vision'
                    
                    if is_image:
                        # Images: Add to message content for model vision
                        image_file_ids.append(file_id)
                        # ALSO add to tool_resources so Python can process the image
                        file_ids_for_code_interpreter.append(file_id)
                    elif file_metadata.purpose == 'assistants':
                        # Non-image documents: Only to tool_resources
                        file_ids_for_code_interpreter.append(file_id)
        
        # Add vision files to message content (MMACTEMP lines 526-528)
        for image_file_id in image_file_ids:
            message_content.append({"type": "image_file", "image_file": {"file_id": image_file_id}})
        
        # Create message using MMACTEMP pattern
        thread_message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message_content  # Use content array like MMACTEMP
        )
        
        # Note: tool_resources in runs.create() not supported in current OpenAI API
        # Files are handled through message content and assistant configuration
        
        # Verify assistant exists in OpenAI before creating run
        print(f"DEBUG: Verifying assistant {message.assistant_id} exists in OpenAI")
        try:
            openai_assistant = client.beta.assistants.retrieve(message.assistant_id)
            print(f"DEBUG: Assistant verified: {openai_assistant.name}")
        except Exception as e:
            print(f"DEBUG: Assistant {message.assistant_id} not found in OpenAI: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Assistant not found in OpenAI: {str(e)}"
            )
        
        print(f"DEBUG: About to create run with assistant_id: {message.assistant_id}")
        try:
            # Create run without tool_resources (not supported in current API)
            run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=message.assistant_id
            )
            print(f"DEBUG: Run created successfully: {run.id}")
        except Exception as e:
            print(f"DEBUG: Error creating run: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create run: {str(e)}"
            )
        
        # Poll to completion (MMACTEMP Pattern C - Option A)
        while True:
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
            if run.status in ("completed", "failed", "cancelled", "expired"):
                break
            await asyncio.sleep(0.8)
        
        if run.status == "completed":
            # Get messages
            messages = client.beta.threads.messages.list(
                thread_id=thread_id,
                limit=1
            )
            
            if messages.data:
                last_message = messages.data[0]
                
                # Extract all content types like MMACTEMP pattern
                content_parts = []
                image_attachments = []
                
                for content in last_message.content:
                    if content.type == 'text':
                        content_parts.append(content.text.value)
                    elif content.type == 'image_file':
                        file_id = content.image_file.file_id
                        # Create URL for our OpenAI file serving endpoint (MMACTEMP pattern)
                        file_url = f"/api/files/openai/{file_id}"
                        image_attachments.append(ImageAttachment(
                            file_id=file_id,
                            type="image",
                            url=file_url,
                            preview_url=file_url,  # Use same URL for preview
                            name=f"image_{file_id}.png",  # Default name
                            size=0,  # We don't have size info from OpenAI response
                            uploaded_at=last_message.created_at or ""
                        ))
                
                text_content = '\n'.join(content_parts) if content_parts else ""
                
                return ChatResponse(
                    message_id=last_message.id,
                    content=text_content,
                    attachments=image_attachments if image_attachments else None
                )
        
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

@router.post("/new-thread")
async def create_new_thread(
    request: NewThreadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new thread for specific assistant (start fresh conversation)"""
    try:
        # Get assistant
        db_assistant = db.query(UserAssistant).filter(
            UserAssistant.assistant_id == request.assistant_id,
            UserAssistant.user_id == current_user.id
        ).first()
        
        if not db_assistant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assistant not found"
            )
        
        # Create new thread for this assistant
        thread = client.beta.threads.create()
        db_assistant.thread_id = thread.id
        db.add(db_assistant)
        db.commit()
        
        return {
            "success": True,
            "thread_id": thread.id,
            "assistant_id": request.assistant_id,
            "message": "New thread created successfully for assistant"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create new thread: {str(e)}"
        )

@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """WebSocket endpoint for streaming chat"""
    await manager.connect(websocket)
    
    try:
        # Verify token and get user
        from jose import jwt
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        
        if not username:
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        # Get user from database
        db = next(get_db())
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            await websocket.close(code=4001, reason="User not found")
            return
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "Connected to chat WebSocket"
        })
        
        # Listen for messages
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "message":
                # Get assistant-specific thread
                db_assistant = db.query(UserAssistant).filter(
                    UserAssistant.assistant_id == data["assistant_id"],
                    UserAssistant.user_id == user.id
                ).first()
                
                if not db_assistant:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Assistant not found"
                    })
                    continue
                
                # Create assistant-specific thread if needed
                if not db_assistant.thread_id:
                    thread = client.beta.threads.create()
                    db_assistant.thread_id = thread.id
                    db.commit()
                
                thread_id = db_assistant.thread_id
                
                # Build message content array like MMACTEMP (lines 493-530)
                message_content = [{"type": "text", "text": data["content"]}]
                image_file_ids = []  # Vision files for message content
                file_ids_for_code_interpreter = []  # Assistant files for tool resources
                
                # Categorize files by purpose (MMACTEMP pattern)
                if data.get("file_ids"):
                    for file_id in data["file_ids"]:
                        # Query database to check file purpose
                        file_metadata = db.query(FileMetadata).filter(
                            FileMetadata.file_id == file_id,
                            FileMetadata.uploaded_by == user.id
                        ).first()
                        
                        if file_metadata:
                            # Check if it's an image by MIME type or purpose
                            is_image = (file_metadata.mime_type and file_metadata.mime_type.startswith('image/')) or file_metadata.purpose == 'vision'
                            
                            if is_image:
                                # Images: Add to message content for model vision
                                image_file_ids.append(file_id)
                                # ALSO add to tool_resources so Python can process the image
                                file_ids_for_code_interpreter.append(file_id)
                            elif file_metadata.purpose == 'assistants':
                                # Non-image documents: Only to tool_resources
                                file_ids_for_code_interpreter.append(file_id)
                
                # Add vision files to message content
                for image_file_id in image_file_ids:
                    message_content.append({"type": "image_file", "image_file": {"file_id": image_file_id}})
                
                # Create the user message with text + image blocks (MMACTEMP Pattern C)
                _ = client.beta.threads.messages.create(
                    thread_id=thread_id,
                    role="user",
                    content=message_content,
                )
                
                # Start a run with ONLY code-interpreter file_ids (not images) (MMACTEMP Pattern C)
                tool_resources = None
                if file_ids_for_code_interpreter:
                    tool_resources = {
                        "code_interpreter": {"file_ids": file_ids_for_code_interpreter}
                    }
                
                # Create event handler with thread ID
                handler = StreamingEventHandler(websocket, thread_id)
                
                # Stream the response using MMACTEMP pattern with tool_resources
                with client.beta.threads.runs.stream(
                    thread_id=thread_id,
                    assistant_id=data["assistant_id"],
                    tool_resources=tool_resources,
                    event_handler=handler,
                ) as stream:
                    stream.until_done()
                
                # Check for image outputs (MMACTEMP pattern)
                await handler.check_for_image_outputs()
                
                # Send completion message
                await websocket.send_json({
                    "type": "complete",
                    "content": handler.full_response
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
        await websocket.close(code=4000, reason=str(e))