"""Assistant management endpoints"""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
import openai
from openai import OpenAI

from models.database import get_db, User, UserAssistant
from api.auth import get_current_user
from utils.config import settings

router = APIRouter()
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Available models
AVAILABLE_MODELS = [
    "gpt-4.1-2025-04-14",  # Latest model for assistants
    "gpt-4.1-mini-2025-04-01",  # Latest mini model
    "gpt-4o",
    "gpt-4o-mini", 
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo"
]

# Pydantic models
class AssistantCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    instructions: str
    model: str = "gpt-4o-mini"
    file_ids: Optional[List[str]] = []

class AssistantUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    model: Optional[str] = None
    file_ids: Optional[List[str]] = None

class AssistantResponse(BaseModel):
    id: int
    assistant_id: str
    name: str
    description: Optional[str]
    instructions: Optional[str]
    model: str
    file_ids: List[str]
    tools: dict = {"web_search": False, "file_search": False, "code_interpreter": True, "computer_use": False}

@router.get("/models")
async def get_available_models():
    """Get list of available OpenAI models"""
    return {"models": AVAILABLE_MODELS}

@router.get("/", response_model=List[AssistantResponse])
async def list_assistants(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's assistants"""
    assistants = db.query(UserAssistant).filter(
        UserAssistant.user_id == current_user.id
    ).all()
    
    return [
        AssistantResponse(
            id=a.id,
            assistant_id=a.assistant_id,
            name=a.name,
            description=a.description,
            instructions=a.instructions,
            model=a.model,
            file_ids=json.loads(a.file_ids) if a.file_ids else [],
            tools={"web_search": False, "file_search": False, "code_interpreter": True, "computer_use": False}
        )
        for a in assistants
    ]

@router.post("/", response_model=AssistantResponse)
async def create_assistant(
    assistant_data: AssistantCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new assistant"""
    try:
        # Create OpenAI assistant with proper tools (MMACTEMP pattern)
        tools = [{"type": "code_interpreter"}]  # Primary tool for file handling
        
        # Deduplicate file IDs like MMACTEMP
        unique_file_ids = list(set(assistant_data.file_ids)) if assistant_data.file_ids else []
        
        # Create with tool_resources if files provided
        if unique_file_ids:
            openai_assistant = client.beta.assistants.create(
                name=assistant_data.name,
                instructions=assistant_data.instructions,
                model=assistant_data.model,
                tools=tools,
                tool_resources={
                    "code_interpreter": {
                        "file_ids": unique_file_ids
                    }
                }
            )
        else:
            openai_assistant = client.beta.assistants.create(
                name=assistant_data.name,
                instructions=assistant_data.instructions,
                model=assistant_data.model,
                tools=tools
            )
        
        # Save to database
        db_assistant = UserAssistant(
            user_id=current_user.id,
            assistant_id=openai_assistant.id,
            name=assistant_data.name,
            description=assistant_data.description,
            instructions=assistant_data.instructions,
            model=assistant_data.model,
            file_ids=json.dumps(assistant_data.file_ids)
        )
        db.add(db_assistant)
        db.commit()
        db.refresh(db_assistant)
        
        return AssistantResponse(
            id=db_assistant.id,
            assistant_id=db_assistant.assistant_id,
            name=db_assistant.name,
            description=db_assistant.description,
            instructions=db_assistant.instructions,
            model=db_assistant.model,
            file_ids=assistant_data.file_ids,
            tools={"web_search": False, "file_search": False, "code_interpreter": True, "computer_use": False}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create assistant: {str(e)}"
        )

@router.put("/{assistant_id}", response_model=AssistantResponse)
async def update_assistant(
    assistant_id: str,
    assistant_update: AssistantUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update assistant"""
    # Get assistant from database
    db_assistant = db.query(UserAssistant).filter(
        UserAssistant.assistant_id == assistant_id,
        UserAssistant.user_id == current_user.id
    ).first()
    
    if not db_assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistant not found"
        )
    
    try:
        # Update OpenAI assistant
        update_data = {}
        if assistant_update.name is not None:
            update_data["name"] = assistant_update.name
            db_assistant.name = assistant_update.name
        if assistant_update.instructions is not None:
            update_data["instructions"] = assistant_update.instructions
            db_assistant.instructions = assistant_update.instructions
        if assistant_update.model is not None:
            update_data["model"] = assistant_update.model
            db_assistant.model = assistant_update.model
        if assistant_update.description is not None:
            db_assistant.description = assistant_update.description
        
        if update_data:
            client.beta.assistants.update(assistant_id, **update_data)
        
        # Update file IDs using MMACTEMP pattern
        if assistant_update.file_ids is not None:
            # Deduplicate file IDs like MMACTEMP
            unique_file_ids = list(set(assistant_update.file_ids)) if assistant_update.file_ids else []
            tools = [{"type": "code_interpreter"}]  # Primary tool for files
            
            # Update assistant with tool_resources (MMACTEMP pattern)
            if unique_file_ids:
                client.beta.assistants.update(
                    assistant_id,
                    tools=tools,
                    tool_resources={
                        "code_interpreter": {
                            "file_ids": unique_file_ids
                        }
                    }
                )
            else:
                # Clear tool_resources if no files
                client.beta.assistants.update(
                    assistant_id,
                    tools=tools,
                    tool_resources={}
                )
            
            db_assistant.file_ids = json.dumps(unique_file_ids)
        
        db.commit()
        db.refresh(db_assistant)
        
        return AssistantResponse(
            id=db_assistant.id,
            assistant_id=db_assistant.assistant_id,
            name=db_assistant.name,
            description=db_assistant.description,
            instructions=db_assistant.instructions,
            model=db_assistant.model,
            file_ids=json.loads(db_assistant.file_ids) if db_assistant.file_ids else [],
            tools={"web_search": False, "file_search": False, "code_interpreter": True, "computer_use": False}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update assistant: {str(e)}"
        )

@router.delete("/{assistant_id}")
async def delete_assistant(
    assistant_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete assistant"""
    # Get assistant from database
    db_assistant = db.query(UserAssistant).filter(
        UserAssistant.assistant_id == assistant_id,
        UserAssistant.user_id == current_user.id
    ).first()
    
    if not db_assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistant not found"
        )
    
    try:
        # Delete from OpenAI
        client.beta.assistants.delete(assistant_id)
        
        # Delete from database
        db.delete(db_assistant)
        db.commit()
        
        return {"message": "Assistant deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete assistant: {str(e)}"
        )