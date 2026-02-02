"""
FastAPI dependencies for authorization
"""
from fastapi import Depends, HTTPException, status

from app.auth import get_current_user
from app.models import User


def admin_required(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to ensure the current user has admin privileges
    
    Args:
        current_user: The authenticated user
        
    Returns:
        The current user if they are an admin
        
    Raises:
        HTTPException: If the user is not an admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

