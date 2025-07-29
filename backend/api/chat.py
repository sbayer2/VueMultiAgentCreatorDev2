"""Chat endpoints with WebSocket support"""
import json
import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from pydantic import BaseModel
from openai import OpenAI, AssistantEventHandler
from openai.types.beta.threads import Message

from models.database import get_db, User
from api.auth import get_current_user
from utils.config import settings
from utils.websocket import ConnectionManager

router = APIRouter()
client = OpenAI(api_key=settings.OPENAI_API_KEY)
manager = ConnectionManager()

class ChatMessage(BaseModel):
    content: str
    assistant_id: str
    file_ids: Optional[list[str]] = []

class ChatResponse(BaseModel):
    message_id: str
    content: str

# Event handler for streaming
class StreamingEventHandler(AssistantEventHandler):
    def __init__(self, websocket: WebSocket):
        super().__init__()
        self.websocket = websocket
        self.full_response = ""
    
    async def on_text_created(self, text):
        await self.websocket.send_json({
            "type": "text_created",
            "content": text.value
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

@router.post("/message", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send message to assistant (non-streaming)"""
    if not current_user.thread_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active thread. Please create a thread first."
        )
    
    try:
        # Add message to thread
        thread_message = client.beta.threads.messages.create(
            thread_id=current_user.thread_id,
            role="user",
            content=message.content,
            file_ids=message.file_ids if message.file_ids else None
        )
        
        # Run assistant
        run = client.beta.threads.runs.create(
            thread_id=current_user.thread_id,
            assistant_id=message.assistant_id
        )
        
        # Wait for completion
        while run.status in ["queued", "in_progress"]:
            await asyncio.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=current_user.thread_id,
                run_id=run.id
            )
        
        if run.status == "completed":
            # Get messages
            messages = client.beta.threads.messages.list(
                thread_id=current_user.thread_id,
                limit=1
            )
            
            if messages.data:
                last_message = messages.data[0]
                content = last_message.content[0].text.value if last_message.content else ""
                return ChatResponse(
                    message_id=last_message.id,
                    content=content
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
            "thread_id": user.thread_id
        })
        
        # Listen for messages
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "message":
                # Create thread if needed
                if not user.thread_id:
                    thread = client.beta.threads.create()
                    user.thread_id = thread.id
                    db.commit()
                
                # Add message to thread
                message = client.beta.threads.messages.create(
                    thread_id=user.thread_id,
                    role="user",
                    content=data["content"],
                    file_ids=data.get("file_ids", [])
                )
                
                # Create event handler
                handler = StreamingEventHandler(websocket)
                
                # Stream the response
                with client.beta.threads.runs.stream(
                    thread_id=user.thread_id,
                    assistant_id=data["assistant_id"],
                    event_handler=handler,
                ) as stream:
                    stream.until_done()
                
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