"""Modern assistant management using OpenAI Responses API"""
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import openai
from openai import OpenAI

from models.database import get_db, User, Assistant, Conversation, ConversationMessage
from api.auth import get_current_user
from utils.config import settings

router = APIRouter()
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Available models for Responses API
AVAILABLE_MODELS = [
    "gpt-4.1-2025-04-14",  # Latest model
    "gpt-4.1-mini-2025-04-01",  # Latest mini model
    "gpt-4o",
    "gpt-4o-mini", 
    "gpt-4o-search-preview",  # For web search
    "gpt-4o-mini-search-preview",
    "computer-use-preview"  # For computer use
]

# Built-in tools configuration
AVAILABLE_TOOLS = {
    "web_search": {"type": "web_search_preview"},
    "file_search": {"type": "file_search"},
    "code_interpreter": {"type": "code_interpreter"},
    "computer_use": {"type": "computer_use_preview"}
}

# Pydantic models
class AssistantToolConfig(BaseModel):
    web_search: bool = False
    file_search: bool = False
    code_interpreter: bool = False
    computer_use: bool = False
    vector_store_ids: Optional[List[str]] = []

class AssistantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    instructions: str = Field(..., min_length=1)
    model: str = Field(default="gpt-4o-mini")
    tools: AssistantToolConfig = Field(default_factory=AssistantToolConfig)

class AssistantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    instructions: Optional[str] = Field(None, min_length=1)
    model: Optional[str] = None
    tools: Optional[AssistantToolConfig] = None

class AssistantResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    instructions: str
    model: str
    tools: AssistantToolConfig
    conversation_count: int = 0
    created_at: str
    updated_at: Optional[str]

class ConversationResponse(BaseModel):
    id: int
    title: Optional[str]
    message_count: int
    last_message_content: Optional[str] = None
    created_at: str
    updated_at: Optional[str]

def _build_tools_config(tools: AssistantToolConfig) -> List[Dict[str, Any]]:
    """Build OpenAI tools configuration from our tool config"""
    tools_list = []
    
    if tools.web_search:
        tools_list.append(AVAILABLE_TOOLS["web_search"])
    
    if tools.file_search and tools.vector_store_ids:
        tools_list.append({
            "type": "file_search",
            "vector_store_ids": tools.vector_store_ids
        })
    
    if tools.code_interpreter:
        tools_list.append(AVAILABLE_TOOLS["code_interpreter"])
    
    if tools.computer_use:
        tools_list.append({
            **AVAILABLE_TOOLS["computer_use"],
            "display_width": 1024,
            "display_height": 768,
            "environment": "browser"
        })
    
    return tools_list

def _parse_tools_config(tools_json: Optional[str]) -> AssistantToolConfig:
    """Parse stored tools configuration"""
    if not tools_json:
        return AssistantToolConfig()
    
    try:
        config = json.loads(tools_json)
        return AssistantToolConfig(**config)
    except:
        return AssistantToolConfig()

@router.get("/models")
async def get_available_models():
    """Get list of available OpenAI models for Responses API"""
    return {"models": AVAILABLE_MODELS}

@router.get("/tools")
async def get_available_tools():
    """Get list of available built-in tools"""
    return {
        "tools": {
            "web_search": {
                "name": "Web Search", 
                "description": "Search the web for current information",
                "pricing": "$25-30 per 1000 queries"
            },
            "file_search": {
                "name": "File Search",
                "description": "Search through uploaded documents",
                "pricing": "$2.50 per 1000 queries + $0.10/GB/day storage"
            },
            "code_interpreter": {
                "name": "Code Interpreter",
                "description": "Execute Python code and analyze data",
                "pricing": "Standard token rates"
            },
            "computer_use": {
                "name": "Computer Use",
                "description": "Interact with web browsers and applications",
                "pricing": "$3/1M input tokens + $12/1M output tokens"
            }
        }
    }

@router.get("/", response_model=List[AssistantResponse])
async def list_assistants(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's modern assistants"""
    assistants = db.query(Assistant).filter(
        Assistant.user_id == current_user.id
    ).all()
    
    response_data = []
    for assistant in assistants:
        tools_config = _parse_tools_config(assistant.tools_config)
        conversation_count = db.query(Conversation).filter(
            Conversation.assistant_id == assistant.id
        ).count()
        
        response_data.append(AssistantResponse(
            id=assistant.id,
            name=assistant.name,
            description=assistant.description,
            instructions=assistant.instructions,
            model=assistant.model,
            tools=tools_config,
            conversation_count=conversation_count,
            created_at=assistant.created_at.isoformat(),
            updated_at=assistant.updated_at.isoformat() if assistant.updated_at else None
        ))
    
    return response_data

@router.post("/", response_model=AssistantResponse)
async def create_assistant(
    assistant_data: AssistantCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new assistant using Responses API approach"""
    
    # Validate model
    if assistant_data.model not in AVAILABLE_MODELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model {assistant_data.model} not supported. Available models: {AVAILABLE_MODELS}"
        )
    
    try:
        # Create assistant in database
        db_assistant = Assistant(
            user_id=current_user.id,
            name=assistant_data.name,
            description=assistant_data.description,
            instructions=assistant_data.instructions,
            model=assistant_data.model,
            tools_config=json.dumps(assistant_data.tools.dict()),
            vector_store_ids=json.dumps(assistant_data.tools.vector_store_ids) if assistant_data.tools.vector_store_ids else None
        )
        
        db.add(db_assistant)
        db.commit()
        db.refresh(db_assistant)
        
        return AssistantResponse(
            id=db_assistant.id,
            name=db_assistant.name,
            description=db_assistant.description,
            instructions=db_assistant.instructions,
            model=db_assistant.model,
            tools=assistant_data.tools,
            conversation_count=0,
            created_at=db_assistant.created_at.isoformat(),
            updated_at=None
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create assistant: {str(e)}"
        )

@router.get("/{assistant_id}", response_model=AssistantResponse)
async def get_assistant(
    assistant_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific assistant"""
    assistant = db.query(Assistant).filter(
        Assistant.id == assistant_id,
        Assistant.user_id == current_user.id
    ).first()
    
    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistant not found"
        )
    
    tools_config = _parse_tools_config(assistant.tools_config)
    conversation_count = db.query(Conversation).filter(
        Conversation.assistant_id == assistant.id
    ).count()
    
    return AssistantResponse(
        id=assistant.id,
        name=assistant.name,
        description=assistant.description,
        instructions=assistant.instructions,
        model=assistant.model,
        tools=tools_config,
        conversation_count=conversation_count,
        created_at=assistant.created_at.isoformat(),
        updated_at=assistant.updated_at.isoformat() if assistant.updated_at else None
    )

@router.put("/{assistant_id}", response_model=AssistantResponse)
async def update_assistant(
    assistant_id: int,
    assistant_update: AssistantUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update assistant"""
    assistant = db.query(Assistant).filter(
        Assistant.id == assistant_id,
        Assistant.user_id == current_user.id
    ).first()
    
    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistant not found"
        )
    
    try:
        # Update fields
        if assistant_update.name is not None:
            assistant.name = assistant_update.name
        if assistant_update.description is not None:
            assistant.description = assistant_update.description
        if assistant_update.instructions is not None:
            assistant.instructions = assistant_update.instructions
        if assistant_update.model is not None:
            if assistant_update.model not in AVAILABLE_MODELS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Model {assistant_update.model} not supported"
                )
            assistant.model = assistant_update.model
        if assistant_update.tools is not None:
            assistant.tools_config = json.dumps(assistant_update.tools.dict())
            assistant.vector_store_ids = json.dumps(assistant_update.tools.vector_store_ids) if assistant_update.tools.vector_store_ids else None
        
        db.commit()
        db.refresh(assistant)
        
        tools_config = _parse_tools_config(assistant.tools_config)
        conversation_count = db.query(Conversation).filter(
            Conversation.assistant_id == assistant.id
        ).count()
        
        return AssistantResponse(
            id=assistant.id,
            name=assistant.name,
            description=assistant.description,
            instructions=assistant.instructions,
            model=assistant.model,
            tools=tools_config,
            conversation_count=conversation_count,
            created_at=assistant.created_at.isoformat(),
            updated_at=assistant.updated_at.isoformat() if assistant.updated_at else None
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update assistant: {str(e)}"
        )

@router.delete("/{assistant_id}")
async def delete_assistant(
    assistant_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete assistant and all associated conversations"""
    assistant = db.query(Assistant).filter(
        Assistant.id == assistant_id,
        Assistant.user_id == current_user.id
    ).first()
    
    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistant not found"
        )
    
    try:
        # Delete assistant (conversations will be cascade deleted)
        db.delete(assistant)
        db.commit()
        
        return {"message": "Assistant deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete assistant: {str(e)}"
        )

@router.get("/{assistant_id}/conversations", response_model=List[ConversationResponse])
async def list_assistant_conversations(
    assistant_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List conversations for an assistant"""
    # Verify assistant ownership
    assistant = db.query(Assistant).filter(
        Assistant.id == assistant_id,
        Assistant.user_id == current_user.id
    ).first()
    
    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistant not found"
        )
    
    conversations = db.query(Conversation).filter(
        Conversation.assistant_id == assistant_id,
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).all()
    
    response_data = []
    for conv in conversations:
        # Get last message content for preview
        last_message = db.query(ConversationMessage).filter(
            ConversationMessage.conversation_id == conv.id
        ).order_by(ConversationMessage.created_at.desc()).first()
        
        response_data.append(ConversationResponse(
            id=conv.id,
            title=conv.title,
            message_count=conv.message_count,
            last_message_content=last_message.content[:100] + "..." if last_message and len(last_message.content) > 100 else last_message.content if last_message else None,
            created_at=conv.created_at.isoformat(),
            updated_at=conv.updated_at.isoformat() if conv.updated_at else None
        ))
    
    return response_data