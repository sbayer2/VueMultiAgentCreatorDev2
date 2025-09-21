"""Assistant management endpoints"""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
import openai
from openai import OpenAI

from models.database import get_db, User, UserAssistant, FileMetadata
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
    model: str = "gpt-4o"  # Default to vision-capable model for MMACTEMP pattern
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
    thread_id: Optional[str] = None
    tools: dict = {"file_search": False, "code_interpreter": True}
    conversation_count: int = 0
    created_at: str
    updated_at: Optional[str] = None

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
    
    result = []
    for a in assistants:
        # Get current file_ids from database
        db_file_ids = json.loads(a.file_ids) if a.file_ids else []
        
        # Sync with OpenAI to get the actual attached files
        try:
            openai_assistant = client.beta.assistants.retrieve(a.assistant_id)
            openai_file_ids = []
            if hasattr(openai_assistant, 'tool_resources') and openai_assistant.tool_resources:
                if hasattr(openai_assistant.tool_resources, 'code_interpreter') and openai_assistant.tool_resources.code_interpreter:
                    if hasattr(openai_assistant.tool_resources.code_interpreter, 'file_ids'):
                        openai_file_ids = openai_assistant.tool_resources.code_interpreter.file_ids or []
            
            print(f"DEBUG: Assistant {a.assistant_id} - DB files: {db_file_ids}, OpenAI files: {openai_file_ids}")
            
            # Use OpenAI's file list since it's the source of truth
            actual_file_ids = openai_file_ids if openai_file_ids else db_file_ids
            
        except Exception as e:
            print(f"DEBUG: Failed to get OpenAI assistant {a.assistant_id}: {e}")
            actual_file_ids = db_file_ids
        
        result.append(AssistantResponse(
            id=a.id,
            assistant_id=a.assistant_id,
            name=a.name,
            description=a.description,
            instructions=a.instructions,
            model=a.model,
            file_ids=actual_file_ids,
            thread_id=a.thread_id,
            tools={"file_search": False, "code_interpreter": True, "vector_store_ids": []},
            conversation_count=0,  # TODO: Implement actual conversation counting
            created_at=a.created_at.isoformat() if a.created_at else ""
        ))
    
    return result

@router.get("/{assistant_id}", response_model=AssistantResponse)
async def get_assistant(
    assistant_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific assistant by its ID."""
    db_assistant = db.query(UserAssistant).filter(
        UserAssistant.assistant_id == assistant_id,
        UserAssistant.user_id == current_user.id
    ).first()
    
    if not db_assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistant not found"
        )
    
    # Get actual OpenAI assistant data to retrieve tool_resources
    try:
        openai_assistant = client.beta.assistants.retrieve(assistant_id)

        # Extract vector store IDs from tool_resources if they exist
        vector_store_ids = []
        if hasattr(openai_assistant, 'tool_resources') and openai_assistant.tool_resources:
            if hasattr(openai_assistant.tool_resources, 'file_search') and openai_assistant.tool_resources.file_search:
                if hasattr(openai_assistant.tool_resources.file_search, 'vector_store_ids'):
                    vector_store_ids = openai_assistant.tool_resources.file_search.vector_store_ids or []

        # Map OpenAI tools to our format (only valid Assistants Beta v2 tools)
        tools_config = {
            "file_search": any(tool.type == 'file_search' for tool in (openai_assistant.tools or [])),
            "code_interpreter": any(tool.type == 'code_interpreter' for tool in (openai_assistant.tools or [])),
            "vector_store_ids": vector_store_ids
        }

    except Exception as e:
        print(f"DEBUG: Failed to get OpenAI assistant {assistant_id}: {e}")
        # Fallback to default tools config (only valid Assistants Beta v2 tools)
        tools_config = {"file_search": False, "code_interpreter": True, "vector_store_ids": []}

    return AssistantResponse(
        id=db_assistant.id,
        assistant_id=db_assistant.assistant_id,
        name=db_assistant.name,
        description=db_assistant.description,
        instructions=db_assistant.instructions,
        model=db_assistant.model,
        file_ids=json.loads(db_assistant.file_ids) if db_assistant.file_ids else [],
        thread_id=db_assistant.thread_id,
        tools=tools_config,
        conversation_count=0,  # TODO: Implement actual conversation counting
        created_at=db_assistant.created_at.isoformat() if db_assistant.created_at else "",
        updated_at=db_assistant.updated_at.isoformat() if db_assistant.updated_at else None
    )

@router.post("/", response_model=AssistantResponse)
async def create_assistant(
    assistant_data: AssistantCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new assistant and automatically create a thread for it."""
    try:
        tools = [{"type": "code_interpreter"}]
        
        unique_file_ids = list(set(assistant_data.file_ids)) if assistant_data.file_ids else []
        tool_resources_file_ids = []

        if unique_file_ids:
            db_files = db.query(FileMetadata).filter(
                FileMetadata.file_id.in_(unique_file_ids),
                FileMetadata.uploaded_by == current_user.id
            ).all()
            tool_resources_file_ids = [f.file_id for f in db_files if f.purpose == 'assistants']

        assistant_params = {
            "name": assistant_data.name,
            "instructions": assistant_data.instructions,
            "model": assistant_data.model,
            "tools": tools
        }
        if tool_resources_file_ids:
            assistant_params["tool_resources"] = {"code_interpreter": {"file_ids": tool_resources_file_ids}}

        openai_assistant = client.beta.assistants.create(**assistant_params)
        
        thread = client.beta.threads.create()
        
        db_assistant = UserAssistant(
            user_id=current_user.id,
            assistant_id=openai_assistant.id,
            name=assistant_data.name,
            description=assistant_data.description,
            instructions=assistant_data.instructions,
            model=assistant_data.model,
            file_ids=json.dumps(unique_file_ids),
            thread_id=thread.id
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
            file_ids=unique_file_ids,
            thread_id=thread.id,
            tools={"file_search": False, "code_interpreter": True, "vector_store_ids": []},
            conversation_count=0,
            created_at=db_assistant.created_at.isoformat() if db_assistant.created_at else ""
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
        
        # Update basic assistant fields if provided
        if update_data:
            try:
                print(f"DEBUG: Updating assistant {assistant_id} basic fields: {update_data}")
                client.beta.assistants.update(assistant_id, **update_data)
                print(f"DEBUG: Successfully updated assistant {assistant_id} basic fields")
            except Exception as e:
                print(f"DEBUG: Failed to update assistant {assistant_id}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to update assistant: {str(e)}"
                )

        # Update file IDs by merging old and new lists
        if assistant_update.file_ids is not None:
            # Get existing files and merge with new ones, ensuring no duplicates
            existing_file_ids = json.loads(db_assistant.file_ids) if db_assistant.file_ids else []
            updated_file_ids = list(set(existing_file_ids + assistant_update.file_ids))

            tools = [{"type": "code_interpreter"}]

            # Separate files by purpose for tool_resources
            db_files = db.query(FileMetadata).filter(
                FileMetadata.file_id.in_(updated_file_ids),
                FileMetadata.uploaded_by == current_user.id
            ).all()

            tool_resources_file_ids = [
                f.file_id for f in db_files if f.purpose == 'assistants'
            ]

            # Update assistant with the complete list of tool files
            try:
                print(f"DEBUG: Updating assistant {assistant_id} file attachments: {tool_resources_file_ids}")
                client.beta.assistants.update(
                    assistant_id,
                    tools=tools,
                    tool_resources={
                        "code_interpreter": {
                            "file_ids": tool_resources_file_ids
                        }
                    } if tool_resources_file_ids else {}
                )
                print(f"DEBUG: Successfully updated assistant {assistant_id} file attachments")
            except Exception as e:
                print(f"DEBUG: Failed to update assistant file attachments: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to update assistant files: {str(e)}"
                )

            # Save the complete, merged list of all file IDs to the database
            db_assistant.file_ids = json.dumps(updated_file_ids)
        
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
            tools={"file_search": False, "code_interpreter": True, "vector_store_ids": []},
            conversation_count=0,
            created_at=db_assistant.created_at.isoformat() if db_assistant.created_at else ""
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

@router.delete("/{assistant_id}/files/{file_id}")
async def remove_file_from_assistant(
    assistant_id: str,
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Detach and delete a file from an assistant and storage."""
    print(f"DEBUG: Attempting to remove file {file_id} from assistant {assistant_id}")
    
    # Verify user owns the assistant
    db_assistant = db.query(UserAssistant).filter(
        UserAssistant.assistant_id == assistant_id,
        UserAssistant.user_id == current_user.id
    ).first()
    if not db_assistant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found")

    # Verify user owns the file metadata
    db_file_meta = db.query(FileMetadata).filter(
        FileMetadata.file_id == file_id,
        FileMetadata.uploaded_by == current_user.id
    ).first()
    if not db_file_meta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found in metadata")

    try:
        # Step 1: Update the assistant to remove the file association
        current_file_ids = json.loads(db_assistant.file_ids) if db_assistant.file_ids else []
        print(f"DEBUG: Current file_ids before removal: {current_file_ids}")
        
        if file_id in current_file_ids:
            current_file_ids.remove(file_id)
            print(f"DEBUG: File {file_id} removed from list. Remaining files: {current_file_ids}")
            
            # We still need to separate by purpose for the tool_resources update
            db_files = db.query(FileMetadata).filter(
                FileMetadata.file_id.in_(current_file_ids),
                FileMetadata.uploaded_by == current_user.id
            ).all()
            tool_resources_file_ids = [f.file_id for f in db_files if f.purpose == 'assistants']
            print(f"DEBUG: Files to keep in tool_resources: {tool_resources_file_ids}")

            # Update OpenAI assistant's tool_resources
            if tool_resources_file_ids:
                print(f"DEBUG: Updating assistant with {len(tool_resources_file_ids)} files")
                client.beta.assistants.update(
                    assistant_id=assistant_id,
                    tool_resources={"code_interpreter": {"file_ids": tool_resources_file_ids}}
                )
                print(f"DEBUG: Successfully updated assistant tool_resources")
            else:
                # When no files left, pass empty list explicitly
                print(f"DEBUG: No files remaining, setting empty tool_resources")
                client.beta.assistants.update(
                    assistant_id=assistant_id,
                    tool_resources={"code_interpreter": {"file_ids": []}}
                )
                print(f"DEBUG: Successfully cleared assistant tool_resources")
            
            # Update database
            db_assistant.file_ids = json.dumps(current_file_ids)
            print(f"DEBUG: Updated database file_ids to: {current_file_ids}")
        else:
            print(f"DEBUG: File {file_id} was not in assistant's file list")

        # Step 2: Delete the file from OpenAI storage
        try:
            print(f"DEBUG: Attempting to delete file {file_id} from OpenAI storage")
            client.files.delete(file_id)
            print(f"DEBUG: Successfully deleted file {file_id} from OpenAI storage")
        except openai.NotFoundError:
            print(f"DEBUG: File {file_id} not found in OpenAI storage (already deleted or never existed)")
            # If file is already deleted from OpenAI, we can proceed
            pass
        except Exception as e:
            print(f"DEBUG: Error deleting file {file_id} from OpenAI: {str(e)}")
            # Continue with database cleanup even if OpenAI delete fails
            pass

        # Step 3: Delete the file metadata from our database
        print(f"DEBUG: Deleting file metadata for {file_id} from database")
        db.delete(db_file_meta)
        
        print(f"DEBUG: Committing all database changes")
        db.commit()
        print(f"DEBUG: Database commit successful")
        
        print(f"DEBUG: File {file_id} removed successfully from assistant {assistant_id}")
        return {"message": "File removed successfully"}

    except Exception as e:
        print(f"DEBUG: Exception occurred during file deletion: {str(e)}")
        print(f"DEBUG: Rolling back database changes")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )