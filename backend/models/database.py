"""Database models and connection setup"""
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from utils.config import settings
import pymysql

# Create base class for models
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    thread_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    legacy_assistants = relationship("UserAssistant", back_populates="user", cascade="all, delete-orphan")

# Legacy table for backwards compatibility during migration
class UserAssistant(Base):
    __tablename__ = "user_assistants"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assistant_id = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    file_ids = Column(Text, nullable=True)  # JSON string
    model = Column(String(50), default="gpt-4o")  # Default to vision-capable model
    thread_id = Column(String(255), nullable=True)  # Assistant-specific thread ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="legacy_assistants")

class FileMetadata(Base):
    __tablename__ = "file_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(255), unique=True, index=True, nullable=False)
    original_name = Column(String(255), nullable=False)
    size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=True)
    purpose = Column(String(50), nullable=False)  # assistants or vision
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Image-specific fields
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    preview_data = Column(Text, nullable=True)  # Base64 encoded thumbnail
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    uploader = relationship("User")

# Modern database models for Responses API (required by auth.py imports)
class Assistant(Base):
    __tablename__ = "assistants"
    
    id = Column(Integer, primary_key=True, index=True)
    assistant_id = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    model = Column(String(50), default="gpt-4o")
    tools = Column(Text, nullable=True)  # JSON string
    tool_resources = Column(Text, nullable=True)  # JSON string
    assistant_metadata = Column(Text, nullable=True)  # JSON string
    temperature = Column(String(10), nullable=True)
    top_p = Column(String(10), nullable=True)
    response_format = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User")
    conversations = relationship("Conversation", back_populates="assistant", cascade="all, delete-orphan")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assistant_id = Column(Integer, ForeignKey("assistants.id"), nullable=False)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    assistant = relationship("Assistant", back_populates="conversations")
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")

class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    message_id = Column(String(255), nullable=True)  # OpenAI message ID
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    attachments = Column(Text, nullable=True)  # JSON string for file attachments
    message_metadata = Column(Text, nullable=True)  # JSON string
    token_count = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

def get_database_url():
    """Get database URL based on environment"""
    # Always use TCP connection with provided host
    import logging
    logger = logging.getLogger(__name__)
    db_url = f"mysql+pymysql://{settings.DB_USER}:{'*' * len(settings.DB_PASS) if settings.DB_PASS else 'NO_PASS'}@{settings.DB_HOST}:3306/{settings.DB_NAME}"
    logger.info(f"Database URL (masked): {db_url}")
    logger.info(f"DB_PASS length: {len(settings.DB_PASS) if settings.DB_PASS else 0}")
    # Add charset for better compatibility
    return f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:3306/{settings.DB_NAME}?charset=utf8mb4"

# Create engine with connection pool settings for Cloud Run
engine = create_engine(
    get_database_url(), 
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    connect_args={
        "connect_timeout": 10
    }
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()