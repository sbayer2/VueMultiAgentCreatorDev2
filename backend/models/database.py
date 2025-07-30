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
    assistants = relationship("UserAssistant", back_populates="user", cascade="all, delete-orphan")

class UserAssistant(Base):
    __tablename__ = "user_assistants"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assistant_id = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    file_ids = Column(Text, nullable=True)  # JSON string
    model = Column(String(50), default="gpt-4o-mini")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="assistants")

class FileMetadata(Base):
    __tablename__ = "file_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(255), unique=True, index=True, nullable=False)
    original_name = Column(String(255), nullable=False)
    size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=True)
    purpose = Column(String(50), nullable=False)  # assistants or vision
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    uploader = relationship("User")

def get_database_url():
    """Get database URL based on environment"""
    # Always use TCP connection with provided host
    import logging
    logger = logging.getLogger(__name__)
    db_url = f"mysql+pymysql://{settings.DB_USER}:{'*' * len(settings.DB_PASS) if settings.DB_PASS else 'NO_PASS'}@{settings.DB_HOST}:3306/{settings.DB_NAME}"
    logger.info(f"Database URL (masked): {db_url}")
    logger.info(f"DB_PASS length: {len(settings.DB_PASS) if settings.DB_PASS else 0}")
    return f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:3306/{settings.DB_NAME}"

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