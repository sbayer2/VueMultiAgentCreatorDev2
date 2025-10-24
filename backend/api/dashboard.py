from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Any, List, Dict

from models.database import get_db, User, UserAssistant
from api.auth import get_current_user

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get dashboard statistics for the current user using the legacy UserAssistant model.
    """
    user_id = current_user.id

    # Get total assistants from the legacy table
    total_assistants = db.query(UserAssistant).filter(UserAssistant.user_id == user_id).count()

    # Count assistants with active threads (conversation_count > 0)
    active_assistants = db.query(UserAssistant).filter(
        UserAssistant.user_id == user_id,
        UserAssistant.thread_id.isnot(None)
    ).count()

    # Placeholder values for other stats
    messages_today = 0
    api_usage = "N/A"

    # Get recent activity
    recent_activity: List[Dict[str, Any]] = []
    
    # Find the last assistant created from the legacy table
    last_assistant = db.query(UserAssistant).filter(UserAssistant.user_id == user_id).order_by(desc(UserAssistant.created_at)).first()
    if last_assistant:
        recent_activity.append({
            "id": f"asst-{last_assistant.id}",
            "title": "New assistant created",
            "description": f"Created \"{last_assistant.name}\"",
            "timestamp": last_assistant.created_at.isoformat(),
        })
        
    # Sort activity by timestamp descending
    recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)

    return {
        "stats": {
            "totalAssistants": total_assistants,
            "activeChats": active_assistants,  # Count of assistants with active threads
            "messagesToday": messages_today,
            "apiUsage": api_usage,
        },
        "recentActivity": recent_activity[:5], # Return latest 5 activities
    }
