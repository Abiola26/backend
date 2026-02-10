"""
Authentication routes
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.auth import (
    authenticate_user, 
    create_access_token, 
    get_current_user, 
    get_password_hash, 
    verify_password,
    settings
)
from app.schemas import (
    Token, 
    UserOut, 
    UserCreate, 
    UserPasswordChange, 
    UserUpdate, 
    PasswordResetRequest, 
    PasswordResetConfirm
)
from app.dependencies import admin_required
from app.models import User
from app import crud
from app.utils.limiter import limiter
from app.utils.email import send_password_reset_email

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/token", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Get JWT access token using OAuth2 password flow
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked. Please contact administrator."
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    
    crud.create_audit_log(db, user.id, user.username, "LOGIN_SUCCESS")
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Get details of current logged in user"""
    return current_user

@router.post("/signup", response_model=UserOut)
def signup(
    user_in: UserCreate, 
    db: Session = Depends(get_db)
):
    """Public signup (Returns 200 as expected by tests)"""
    user = crud.get_user_by_username(db, user_in.username)
    if user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    if user_in.email:
        email_user = db.query(User).filter(User.email == user_in.email).first()
        if email_user:
            raise HTTPException(status_code=400, detail="Email already registered")
            
    # Force role to "user" for public signup
    user_in.role = "user"
            
    return crud.create_user(
        db, 
        username=user_in.username, 
        password=user_in.password, 
        role=user_in.role, 
        email=user_in.email
    )

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserCreate, 
    db: Session = Depends(get_db),
    _: User = Depends(admin_required)
):
    """Register a new user (Admin only)"""
    user = crud.get_user_by_username(db, user_in.username)
    if user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    if user_in.email:
        email_user = db.query(User).filter(User.email == user_in.email).first()
        if email_user:
            raise HTTPException(status_code=400, detail="Email already registered")
            
    return crud.create_user(
        db, 
        username=user_in.username, 
        password=user_in.password, 
        role=user_in.role, 
        email=user_in.email
    )

@router.get("/users", response_model=List[UserOut])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(admin_required)
):
    """List all users (Admin only)"""
    return crud.get_users(db, skip=skip, limit=limit)

@router.get("/users/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(admin_required)
):
    """Get user by ID (Admin only)"""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    """Update user details (Admin only)"""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_update.username:
        # Check if new username is taken
        existing = db.query(User).filter(User.username == user_update.username, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        user.username = user_update.username
        
    if user_update.email:
        user.email = user_update.email
        
    if user_update.role:
        user.role = user_update.role
    
    if user_update.account_id:
        user.account_id = user_update.account_id
        
    db.commit()
    db.refresh(user)
    return user

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    """Delete a user (Admin only)"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
        
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}


@router.post("/password-reset-request")
@limiter.limit("3/minute")
async def password_reset_request(
    request: Request,
    reset_request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Request a password reset token"""
    user = db.query(User).filter(User.email == reset_request.email).first()
    if not user:
        # For security, don't confirm if user exists or not
        return {"message": "If an account exists for this email, a reset token has been sent."}
        
    reset_token = create_access_token(
        data={"sub": user.username, "purpose": "password_reset"},
        expires_delta=timedelta(minutes=15),
    )
    
    background_tasks.add_task(send_password_reset_email, user.email, reset_token)
    crud.create_audit_log(db, user.id, user.username, "PASSWORD_RESET_REQUESTED")
    
    return {"message": "If an account exists for this email, a reset token has been sent."}


@router.post("/password-reset-confirm")
def password_reset_confirm(
    confirm: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirm password reset with token"""
    from jose import jwt, JWTError
    from app.config import get_settings
    settings = get_settings()
    
    try:
        payload = jwt.decode(confirm.token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        purpose: str = payload.get("purpose")
        
        if username is None or purpose != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid token")
            
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.hashed_password = get_password_hash(confirm.new_password)
    user.is_locked = False
    user.failed_login_attempts = 0
    db.commit()
    
    crud.create_audit_log(db, user.id, user.username, "PASSWORD_RESET_COMPLETED")
    
    return {"message": "Password reset successfully"}