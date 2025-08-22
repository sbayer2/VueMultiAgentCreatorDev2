"""Authentication endpoints"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from models.database import get_db, User
from utils.config import settings

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# Pydantic models
class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    thread_id: Optional[str]

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    confirmPassword: str

class AuthResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[dict] = None

@router.post("/register")
async def register(register_data: RegisterRequest, db: Session = Depends(get_db)):
    """Register new user"""
    # Validate passwords match
    if register_data.password != register_data.confirmPassword:
        return AuthResponse(
            success=False, 
            error={"message": "Passwords do not match"}
        )
    
    # Check if user exists
    db_user = db.query(User).filter(User.username == register_data.email).first()
    if db_user:
        return AuthResponse(
            success=False,
            error={"message": "Email already registered"}
        )
    
    # Create new user
    hashed_password = get_password_hash(register_data.password)
    db_user = User(username=register_data.email, password_hash=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username}, expires_delta=access_token_expires
    )
    
    return AuthResponse(
        success=True,
        data={
            "token": access_token,
            "user": {
                "id": db_user.id,
                "email": db_user.username,
                "name": register_data.name
            }
        }
    )

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login user"""
    user = db.query(User).filter(User.username == login_data.email).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        return AuthResponse(
            success=False,
            error={"message": "Invalid email or password"}
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return AuthResponse(
        success=True,
        data={
            "token": access_token,
            "user": {
                "id": user.id,
                "email": user.username,
                "name": user.username.split('@')[0]  # Use email prefix as name
            }
        }
    )

@router.post("/token", response_model=Token)
async def token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 token endpoint for Swagger UI"""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout():
    """Logout user (client-side token removal)"""
    return {"success": True, "message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        thread_id=current_user.thread_id
    )

@router.delete("/account")
async def delete_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete user account"""
    db.delete(current_user)
    db.commit()
    return {"message": "Account deleted successfully"}

# Temporary endpoint for testing - remove in production
@router.delete("/reset-all-users-test-only")
async def reset_all_users(db: Session = Depends(get_db)):
    """Delete all users and related data - FOR TESTING ONLY"""
    try:
        from models.database import UserAssistant, Assistant, Conversation, ConversationMessage, FileMetadata
        
        # Get count before deletion
        user_count = db.query(User).count()
        
        # Delete in order to respect foreign key constraints
        db.query(ConversationMessage).delete()
        db.query(Conversation).delete() 
        db.query(FileMetadata).delete()
        db.query(Assistant).delete()
        db.query(UserAssistant).delete()
        db.query(User).delete()
        
        db.commit()
        return {"success": True, "message": f"Deleted {user_count} users and all related data"}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}