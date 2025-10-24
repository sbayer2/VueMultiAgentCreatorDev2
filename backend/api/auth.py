"""Authentication endpoints"""
from datetime import datetime, timedelta
from typing import Optional
import secrets
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

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
                "name": db_user.username.split('@')[0]  # Use email prefix as name
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
class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    password: str

def create_reset_token(email: str) -> str:
    """Create a password reset token"""
    # Create a token with email and expiry embedded
    from datetime import timezone
    data = {
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),  # Token expires in 1 hour
        "type": "password_reset"
    }
    token = jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token

def verify_reset_token(token: str) -> Optional[str]:
    """Verify password reset token and return email if valid"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "password_reset":
            return None
        email = payload.get("email")
        return email
    except JWTError:
        return None

def send_email_sync(to_email: str, subject: str, body: str):
    """Synchronously send email via SMTP"""
    try:
        # Only send email if SMTP is configured
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            print(f"Email not configured. Would send to {to_email}: {subject}")
            print(f"Reset URL: {body}")
            return

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.FROM_EMAIL or settings.SMTP_USER
        msg['To'] = to_email

        # Create HTML version
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #333;">Password Reset Request</h2>
            <p>You requested to reset your password. Click the link below to set a new password:</p>
            <p style="margin: 30px 0;">
              <a href="{body}" style="background-color: #4CAF50; color: white; padding: 14px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">
                Reset Password
              </a>
            </p>
            <p style="color: #666; font-size: 14px;">Or copy and paste this link into your browser:</p>
            <p style="color: #666; font-size: 14px; word-break: break-all;">{body}</p>
            <p style="color: #666; font-size: 14px; margin-top: 30px;">This link will expire in 1 hour.</p>
            <p style="color: #666; font-size: 14px;">If you didn't request this, please ignore this email.</p>
          </body>
        </html>
        """

        # Create plain text version
        text_body = f"""
Password Reset Request

You requested to reset your password. Visit this link to set a new password:

{body}

This link will expire in 1 hour.

If you didn't request this, please ignore this email.
        """

        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')

        msg.attach(part1)
        msg.attach(part2)

        # Send email
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        print(f"Password reset email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {str(e)}")
        # Log the URL as fallback
        print(f"Password reset URL for {to_email}: {body}")

async def send_password_reset_email(email: str, reset_url: str, background_tasks: BackgroundTasks):
    """Send password reset email asynchronously"""
    background_tasks.add_task(send_email_sync, email, "Reset Your Password", reset_url)

@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Request password reset"""
    # Check if user exists
    user = db.query(User).filter(User.username == request.email).first()

    # Always return success to prevent email enumeration
    if user:
        # Create reset token
        token = create_reset_token(request.email)

        # In production, use actual frontend URL from environment variable
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        reset_url = f"{frontend_url}/reset-password?token={token}"

        # Send email (async)
        await send_password_reset_email(request.email, reset_url, background_tasks)

    return AuthResponse(
        success=True,
        data={"message": "If an account exists with that email, we've sent you a password reset link."}
    )

@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Reset password with token"""
    print(f"DEBUG: Reset password request received")
    print(f"DEBUG: Token length: {len(request.token)}")

    # Verify token
    email = verify_reset_token(request.token)
    if not email:
        print(f"DEBUG: Token verification failed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    print(f"DEBUG: Token verified for email: {email}")

    # Find user
    user = db.query(User).filter(User.username == email).first()
    if not user:
        print(f"DEBUG: User not found for email: {email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )

    print(f"DEBUG: User found: {user.id}, updating password")

    # Update password
    user.password_hash = get_password_hash(request.password)
    db.commit()

    print(f"DEBUG: Password updated successfully for user: {email}")

    return AuthResponse(
        success=True,
        data={"message": "Password reset successfully"}
    )

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