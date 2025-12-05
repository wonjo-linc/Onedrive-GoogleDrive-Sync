"""
Account management routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import List

from src.database.session import get_db
from src.database.models import User, ConnectedAccount
from src.api.session_deps import get_current_user

router = APIRouter(prefix="/accounts", tags=["accounts"])


class AccountResponse(BaseModel):
    id: int
    platform: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[AccountResponse])
async def list_accounts(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List connected accounts"""
    accounts = db.query(ConnectedAccount).filter(
        ConnectedAccount.user_id == user.id
    ).all()
    return accounts


@router.delete("/{account_id}")
async def disconnect_account(
    account_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnect account"""
    account = db.query(ConnectedAccount).filter(
        ConnectedAccount.id == account_id,
        ConnectedAccount.user_id == user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    db.delete(account)
    db.commit()
    
    return {"message": "Account disconnected successfully"}
