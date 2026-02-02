"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import authenticate_user, create_access_token, get_current_user, get_password_hash, verify_password
from app.schemas import Token, UserOut, UserCreate, UserPasswordChange, UserUpdate, PasswordResetRequest, PasswordResetConfirm
from app.dependencies import admin_required
from app.models import User
from app import crud
from app.utils import generate_account_id
from app.utils.email import send_password_reset_email
from fastapi import BackgroundTasks

from app.utils.limiter import limiter
from fastapi import Request

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/token", response_model=Token)
@limiter.limit("5/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login endpoint
    
    Returns a JWT access token for authenticated users
    """
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        # Check if the user exists to log the lock status if they just got locked
        u = db.query(User).filter(User.username == form_data.username).first()
        if u and u.is_locked:
            crud.create_audit_log(db, u.id, u.username, "ACCOUNT_LOCKED", "Too many failed attempts")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is locked due to too many failed attempts. Contact admin."
            )
            
        crud.create_audit_log(db, None, form_data.username, "LOGIN_FAILED")
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
        
    crud.create_audit_log(db, user.id, user.username, "LOGIN_SUCCESS")

    access_token = create_access_token(data={"sub": user.username})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


@router.post("/signup", response_model=UserOut)
@limiter.limit("3/minute")
def register_user(
    request: Request,
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Public registration endpoint
    """
    # Check if user exists
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    if user_in.email:
        if db.query(User).filter(User.email == user_in.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
    
    user = crud.create_user(
        db, 
        username=user_in.username, 
        password=user_in.password, 
        role="user",
        email=user_in.email
    )
    
    crud.create_audit_log(db, user.id, user.username, "SIGNUP")
    crud.create_notification(
        db, 
        title="Welcome to FRAS!", 
        message=f"Hello {user.username}, your account has been successfully created. Explore the dashboard to get started.",
        type="success",
        user_id=user.id
    )
    return user


@router.post("/register", response_model=UserOut)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    """
    Create a new user (Admin only)
    """
    # Check if user exists
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    hashed_pw = get_password_hash(user_in.password)
    
    # Generate Account ID
    account_id = generate_account_id(user_in.role)

    new_user = User(
        username=user_in.username,
        hashed_password=hashed_pw,
        role=user_in.role,
        account_id=account_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    crud.create_audit_log(db, current_user.id, current_user.username, "CREATE_USER", f"Created user: {new_user.username}")
    
    return new_user


@router.post("/change-password")
def change_password(
    password_in: UserPasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Change current user password"""
    if not verify_password(password_in.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="Incorrect current password"
        )
        
    current_user.hashed_password = get_password_hash(password_in.new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}


@router.get("/users", response_model=list[UserOut])
def get_all_users(
    db: Session = Depends(get_db),
    _: User = Depends(admin_required)
):
    """List all users (Admin only)"""
    return db.query(User).all()


@router.put("/me", response_model=UserOut)
def update_profile(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update current user profile"""
    if user_update.username:
        # Check if username exists and it's not the current user
        existing = db.query(User).filter(User.username == user_update.username).first()
        if existing and existing.id != current_user.id:
            raise HTTPException(status_code=400, detail="Username already taken")
        current_user.username = user_update.username
    
    if user_update.email:
        # Check if email is already taken
        existing_email = db.query(User).filter(User.email == user_update.email).first()
        if existing_email and existing_email.id != current_user.id:
            raise HTTPException(status_code=400, detail="Email already registered")
        current_user.email = user_update.email
    
    # Only admins can update role via this endpoint (or any endpoint)
    # Actually, let's keep it simple: users only update their username here.
    # Role and Account ID updates are for /users/{id}
    
    db.commit()
    db.refresh(current_user)
    
    crud.create_audit_log(db, current_user.id, current_user.username, "UPDATE_PROFILE", "Updated profile details")
    
    return current_user


@router.put("/users/{user_id}", response_model=UserOut)
def update_user_role(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(admin_required)
):
    """Update user role (Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
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
    _: User = Depends(admin_required)
):
    """Delete a user (Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}
@router.post("/password-reset-request")
@limiter.limit("3/minute")
async def password_reset_request(
    request: Request,
    reset_request: PasswordResetRequest, # Renamed request to reset_request to avoid conflict with Request
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Request a password reset token
    """
    user = db.query(User).filter(User.email == reset_request.email).first()
    if not user:
        # For security, we usually return success even if email not found
        # but for this dev stage, let's be explicit
        raise HTTPException(status_code=404, detail="User with this email not found")
        
    # Generate a short-lived token (15 mins)
    reset_token = create_access_token(
        data={"sub": user.username, "purpose": "password_reset"}
    )
    
    # Send email in background
    background_tasks.add_task(send_password_reset_email, user.email, reset_token)
    
    crud.create_audit_log(db, user.id, user.username, "PASSWORD_RESET_REQUESTED")
    
    return {
        "message": "If an account exists for this email, a reset token has been sent.",
        "token": reset_token  # Still returning for dev convenience
    }


@router.post("/password-reset-confirm")
def password_reset_confirm(
    confirm: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Confirm password reset with token
    """
    from jose import jwt, JWTError
    from app.auth import SECRET_KEY, ALGORITHM
    
    try:
        payload = jwt.decode(confirm.token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        purpose: str = payload.get("purpose")
        
        if username is None or purpose != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid token")
            
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
        
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.hashed_password = get_password_hash(confirm.new_password)
    user.failed_login_attempts = 0
    user.is_locked = False
    db.commit()
    
    crud.create_audit_log(db, user.id, user.username, "PASSWORD_RESET_SUCCESS")
    crud.create_notification(
        db,
        title="Password Reset Successful",
        message="Your password has been changed successfully. If you did not perform this action, please contact support immediately.",
        type="warning",
        user_id=user.id
    )
    
    return {"message": "Password has been reset successfully. You can now login."}
