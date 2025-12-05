"""
Session-based authentication dependencies
"""

from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
from src.database.session import get_db
from src.database.models import User


async def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Get current user from session"""
    user_id = request.session.get('user_id')
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user
