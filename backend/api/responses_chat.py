"""Modern chat system using OpenAI Responses API with cost optimization"""
import json
import asyncio
from typing import Optional, List, Dict, Any, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from openai import OpenAI, AsyncOpenAI
import openai

from models.database import get_db, User, Assistant, Conversation, ConversationMessage
from api.auth import get_current_user
from utils.config import settings
from utils.websocket import ConnectionManager

router = APIRouter()
client = OpenAI(api_key=settings.OPENAI_API_KEY)
async_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
manager = ConnectionManager()

# Cost optimization settings
MAX_CONVERSATION_LENGTH = 50  # Limit conversation length to manage costs
CONTEXT_WINDOW_SIZE = 20     # Only include last N messages for context

class ChatMessage(BaseModel):
    content: str = Field(..., min_length=1)
    assistant_id: int
    conversation_id: Optional[int] = None
    attachments: Optional[List[Dict[str, Any]]] = None

class ChatResponse(BaseModel):
    message_id: int
    conversation_id: int
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tokens_used: Optional[int] = None
    response_id: Optional[str] = None

class ConversationCreate(BaseModel):
    assistant_id: int
    title: Optional[str] = None

class ConversationResponse(BaseModel):
    id: int
    assistant_id: int
    title: Optional[str]
    message_count: int
    created_at: str
    updated_at: Optional[str]

class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    tokens_used: Optional[int] = None
    created_at: str

def _build_conversation_input(messages: List[ConversationMessage], new_content: str, new_attachments: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """Build input for Responses API with image support and cost optimization"""
    
    # Limit context window to manage costs
    recent_messages = messages[-CONTEXT_WINDOW_SIZE:] if len(messages) > CONTEXT_WINDOW_SIZE else messages
    
    input_messages = []
    
    # Add conversation history
    for msg in recent_messages:
        message_content = []
        
        # Add text content
        if msg.content:
            message_content.append({
                "type": "text",
                "text": msg.content
            })
        
        # Add image attachments if present
        if msg.attachments:
            try:
                attachments = json.loads(msg.attachments) if isinstance(msg.attachments, str) else msg.attachments
                for attachment in attachments:
                    if attachment.get('file_id'):
                        message_content.append({
                            "type": "image_file",
                            "image_file": {
                                "file_id": attachment['file_id']
                            }
                        })
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error parsing attachments for message {msg.id}: {e}")
        
        # Use simple string content if no attachments, otherwise use content array
        input_messages.append({
            "role": msg.role,
            "content": msg.content if not message_content or len(message_content) == 1 else message_content
        })
    
    # Add new user message with potential attachments
    new_message_content = []
    
    # Add text content
    if new_content:
        new_message_content.append({
            "type": "text", 
            "text": new_content
        })
    
    # Add new image attachments
    if new_attachments:
        for attachment in new_attachments:
            if attachment.get('file_id'):
                new_message_content.append({
                    "type": "image_file",
                    "image_file": {
                        "file_id": attachment['file_id']
                    }
                })
    
    # Use simple string or content array based on presence of attachments
    input_messages.append({
        "role": "user",
        "content": new_content if not new_message_content or len(new_message_content) == 1 else new_message_content
    })
    
    return input_messages

def _build_tools_for_assistant(assistant: Assistant) -> List[Dict[str, Any]]:
    """Build tools configuration for Responses API call"""
    if not assistant.tools_config:
        return []
    
    try:
        tools_config = json.loads(assistant.tools_config)
        tools_list = []
        
        if tools_config.get("web_search"):
            tools_list.append({"type": "web_search_preview"})
        
        if tools_config.get("file_search") and assistant.vector_store_ids:
            vector_store_ids = json.loads(assistant.vector_store_ids)
            tools_list.append({
                "type": "file_search",
                "vector_store_ids": vector_store_ids
            })
        
        if tools_config.get("code_interpreter"):
            tools_list.append({"type": "code_interpreter"})
        
        if tools_config.get("computer_use"):
            tools_list.append({
                "type": "computer_use_preview",
                "display_width": 1024,
                "display_height": 768,
                "environment": "browser"
            })
        
        return tools_list
    except:
        return []

@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation"""
    # Verify assistant ownership
    assistant = db.query(Assistant).filter(
        Assistant.id == conversation_data.assistant_id,
        Assistant.user_id == current_user.id
    ).first()
    
    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistant not found"
        )
    
    try:
        conversation = Conversation(
            user_id=current_user.id,
            assistant_id=conversation_data.assistant_id,
            title=conversation_data.title or f"Conversation with {assistant.name}",
            message_count=0
        )
        
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        return ConversationResponse(
            id=conversation.id,
            assistant_id=conversation.assistant_id,
            title=conversation.title,
            message_count=0,
            created_at=conversation.created_at.isoformat(),
            updated_at=None
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create conversation: {str(e)}"
        )

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get messages in a conversation"""
    # Verify conversation ownership
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    messages = db.query(ConversationMessage).filter(
        ConversationMessage.conversation_id == conversation_id
    ).order_by(ConversationMessage.created_at.asc()).all()
    
    return [
        MessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            tool_calls=json.loads(msg.tool_calls) if msg.tool_calls else None,
            attachments=json.loads(msg.attachments) if msg.attachments else None,
            tokens_used=msg.tokens_used,
            created_at=msg.created_at.isoformat()
        )
        for msg in messages
    ]

@router.post("/conversations/{conversation_id}/messages", response_model=ChatResponse)
async def send_message(
    conversation_id: int,
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send message using Responses API with cost optimization"""
    
    # Verify conversation and assistant ownership
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    assistant = db.query(Assistant).filter(
        Assistant.id == conversation.assistant_id,
        Assistant.user_id == current_user.id
    ).first()
    
    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistant not found"
        )
    
    # Cost protection: Check conversation length
    if conversation.message_count >= MAX_CONVERSATION_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Conversation has reached maximum length of {MAX_CONVERSATION_LENGTH} messages. Please start a new conversation to manage costs."
        )
    
    try:
        # Get conversation history
        messages = db.query(ConversationMessage).filter(
            ConversationMessage.conversation_id == conversation_id
        ).order_by(ConversationMessage.created_at.asc()).all()
        
        # Build input with cost optimization and image support
        conversation_input = _build_conversation_input(messages, message.content, message.attachments)
        
        # Build tools configuration
        tools = _build_tools_for_assistant(assistant)
        
        # Prepare Responses API call
        response_params = {
            "model": assistant.model,
            "instructions": assistant.instructions,
            "input": conversation_input,
        }
        
        if tools:
            response_params["tools"] = tools
        
        # Add previous_response_id for conversation continuity (CRITICAL for cost management)
        if conversation.last_response_id:
            response_params["previous_response_id"] = conversation.last_response_id
        
        # Call OpenAI Responses API
        response = client.responses.create(**response_params)
        
        # Save user message with attachments
        user_message = ConversationMessage(
            conversation_id=conversation_id,
            role="user",
            content=message.content,
            attachments=json.dumps(message.attachments) if message.attachments else None
        )
        db.add(user_message)
        
        # Extract response content
        response_content = response.output_text if hasattr(response, 'output_text') else str(response.output)
        
        # Extract tool calls if any
        tool_calls = None
        if hasattr(response, 'tool_calls') and response.tool_calls:
            tool_calls = [tool_call.dict() for tool_call in response.tool_calls]
        
        # Save assistant message
        assistant_message = ConversationMessage(
            conversation_id=conversation_id,
            response_id=response.id if hasattr(response, 'id') else None,
            role="assistant",
            content=response_content,
            tool_calls=json.dumps(tool_calls) if tool_calls else None,
            tokens_used=getattr(response, 'usage', {}).get('total_tokens') if hasattr(response, 'usage') else None
        )
        db.add(assistant_message)
        
        # Update conversation
        conversation.last_response_id = response.id if hasattr(response, 'id') else None
        conversation.message_count += 2  # User + Assistant message
        
        db.commit()
        db.refresh(assistant_message)
        
        return ChatResponse(
            message_id=assistant_message.id,
            conversation_id=conversation_id,
            content=response_content,
            tool_calls=tool_calls,
            tokens_used=assistant_message.tokens_used,
            response_id=assistant_message.response_id
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to send message: {str(e)}"
        )

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation and all its messages"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    try:
        db.delete(conversation)  # Messages will cascade delete
        db.commit()
        
        return {"message": "Conversation deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete conversation: {str(e)}"
        )

# WebSocket endpoint for streaming responses
@router.websocket("/conversations/{conversation_id}/stream")
async def websocket_chat_endpoint(websocket: WebSocket, conversation_id: int):
    """WebSocket endpoint for streaming chat with Responses API"""
    try:
        await manager.connect(websocket, conversation_id)
        
        # Get token from query parameters or headers
        token = None
        if "token" in websocket.query_params:
            token = websocket.query_params["token"]
        elif "Authorization" in websocket.headers:
            auth_header = websocket.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
        
        if not token:
            await websocket.close(code=4001, reason="No token provided")
            return
        
        # Verify token and get user
        try:
            from jose import jwt
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username = payload.get("sub")
            
            if not username:
                await websocket.close(code=4001, reason="Invalid token")
                return
        except Exception as e:
            await websocket.close(code=4001, reason="Invalid token format")
            return
        
        # Get database session
        db_session = next(get_db())
        
        try:
            # Get user
            user = db_session.query(User).filter(User.username == username).first()
            if not user:
                await websocket.close(code=4001, reason="User not found")
                return
            
            # Get and verify conversation ownership
            conversation = db_session.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user.id
            ).first()
            
            if not conversation:
                await websocket.close(code=4001, reason="Conversation not found")
                return
            
            # Get assistant
            assistant = db_session.query(Assistant).filter(
                Assistant.id == conversation.assistant_id
            ).first()
            
            if not assistant:
                await websocket.close(code=4001, reason="Assistant not found")
                return
            
            # Send connection confirmation
            await websocket.send_json({
                "type": "connection",
                "status": "connected",
                "conversation_id": conversation_id,
                "message_count": conversation.message_count
            })
            
            # Message handling loop
            while True:
                try:
                    data = await websocket.receive_json()
                    
                    if data.get("type") == "message":
                        content = data.get("content", "").strip()
                        attachments = data.get("attachments", [])
                        
                        if not content and not attachments:
                            await websocket.send_json({
                                "type": "error",
                                "message": "Message content or attachments required"
                            })
                            continue
                        
                        # Cost protection check
                        if conversation.message_count >= MAX_CONVERSATION_LENGTH:
                            await websocket.send_json({
                                "type": "error",
                                "message": f"Conversation has reached maximum length of {MAX_CONVERSATION_LENGTH} messages."
                            })
                            continue
                        
                        # Get conversation history
                        messages = db_session.query(ConversationMessage).filter(
                            ConversationMessage.conversation_id == conversation_id
                        ).order_by(ConversationMessage.created_at.asc()).all()
                        
                        # Build input for Responses API with image support
                        conversation_input = _build_conversation_input(messages, content, attachments)
                        tools = _build_tools_for_assistant(assistant)
                        
                        # Prepare streaming response parameters
                        response_params = {
                            "model": assistant.model,
                            "instructions": assistant.instructions,
                            "input": conversation_input,
                            "stream": True
                        }
                        
                        if tools:
                            response_params["tools"] = tools
                        
                        if conversation.last_response_id:
                            response_params["previous_response_id"] = conversation.last_response_id
                        
                        # Save user message first with attachments
                        user_message = ConversationMessage(
                            conversation_id=conversation_id,
                            role="user",
                            content=content,
                            attachments=json.dumps(attachments) if attachments else None
                        )
                        db_session.add(user_message)
                        db_session.commit()
                        
                        # Stream response from OpenAI
                        full_response = ""
                        response_id = None
                        tool_calls = []
                        
                        try:
                            async for chunk in async_client.responses.create(**response_params):
                                if hasattr(chunk, 'type'):
                                    # Handle text streaming
                                    if chunk.type == 'response.text.delta':
                                        delta_content = getattr(chunk, 'delta', '') or getattr(chunk, 'text', '') or ''
                                        if delta_content:
                                            full_response += delta_content
                                            await websocket.send_json({
                                                "type": "text_delta",
                                                "content": delta_content
                                            })
                                    
                                    # Handle tool calls
                                    elif chunk.type == 'response.tool_call.start':
                                        await websocket.send_json({
                                            "type": "tool_call_start",
                                            "tool_name": getattr(chunk, 'tool_name', 'unknown')
                                        })
                                    
                                    elif chunk.type == 'response.tool_call.delta':
                                        await websocket.send_json({
                                            "type": "tool_call_delta",
                                            "content": getattr(chunk, 'delta', '')
                                        })
                                    
                                    elif chunk.type == 'response.tool_call.done':
                                        if hasattr(chunk, 'tool_call'):
                                            tool_calls.append(chunk.tool_call.dict())
                                        await websocket.send_json({
                                            "type": "tool_call_complete",
                                            "tool_name": getattr(chunk, 'tool_name', 'unknown')
                                        })
                                    
                                    # Handle response completion
                                    elif chunk.type == 'response.done':
                                        response_id = getattr(chunk, 'id', None)
                                        
                                        await websocket.send_json({
                                            "type": "complete",
                                            "content": full_response,
                                            "response_id": response_id
                                        })
                                        break
                        
                        except Exception as stream_error:
                            await websocket.send_json({
                                "type": "error",
                                "message": f"Streaming error: {str(stream_error)}"
                            })
                            continue
                        
                        # Save assistant message
                        try:
                            assistant_message = ConversationMessage(
                                conversation_id=conversation_id,
                                response_id=response_id,
                                role="assistant",
                                content=full_response,
                                tool_calls=json.dumps(tool_calls) if tool_calls else None
                            )
                            db_session.add(assistant_message)
                            
                            # Update conversation
                            conversation.last_response_id = response_id
                            conversation.message_count += 2  # User + Assistant
                            
                            db_session.commit()
                        
                        except Exception as db_error:
                            db_session.rollback()
                            await websocket.send_json({
                                "type": "error",
                                "message": f"Database error: {str(db_error)}"
                            })
                    
                    elif data.get("type") == "ping":
                        # Handle heartbeat
                        await websocket.send_json({"type": "pong"})
                    
                except WebSocketDisconnect:
                    break
                except Exception as msg_error:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Message processing error: {str(msg_error)}"
                    })
        
        finally:
            db_session.close()
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Connection error: {str(e)}"
            })
        except:
            pass
        try:
            await websocket.close(code=4000, reason=str(e))
        except:
            pass
    finally:
        manager.disconnect(websocket, conversation_id)