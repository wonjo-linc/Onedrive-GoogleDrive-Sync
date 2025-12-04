"""
Sync jobs management routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

from src.database.session import get_db
from src.database.models import User, SyncJob, ConnectedAccount
from src.api.dependencies import get_current_user

router = APIRouter(prefix="/sync-jobs", tags=["sync-jobs"])


class SyncJobCreate(BaseModel):
    name: str
    onedrive_account_id: int
    gdrive_account_id: int
    onedrive_folder: str
    gdrive_folder: str
    direction: str = "bidirectional"  # 'bidirectional', 'onedrive_to_gdrive', 'gdrive_to_onedrive'


class SyncJobUpdate(BaseModel):
    name: Optional[str] = None
    onedrive_folder: Optional[str] = None
    gdrive_folder: Optional[str] = None
    direction: Optional[str] = None
    enabled: Optional[bool] = None


class SyncJobResponse(BaseModel):
    id: int
    name: str
    onedrive_account_id: int
    gdrive_account_id: int
    onedrive_folder: str
    gdrive_folder: str
    direction: str
    enabled: bool
    created_at: datetime
    last_sync: Optional[datetime]
    
    class Config:
        from_attributes = True


@router.post("/", response_model=SyncJobResponse, status_code=status.HTTP_201_CREATED)
async def create_sync_job(
    job_data: SyncJobCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new sync job"""
    
    # Verify accounts belong to user
    onedrive_account = db.query(ConnectedAccount).filter(
        ConnectedAccount.id == job_data.onedrive_account_id,
        ConnectedAccount.user_id == user.id,
        ConnectedAccount.platform == 'onedrive'
    ).first()
    
    if not onedrive_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OneDrive account not found"
        )
    
    gdrive_account = db.query(ConnectedAccount).filter(
        ConnectedAccount.id == job_data.gdrive_account_id,
        ConnectedAccount.user_id == user.id,
        ConnectedAccount.platform == 'gdrive'
    ).first()
    
    if not gdrive_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Google Drive account not found"
        )
    
    # Create sync job
    sync_job = SyncJob(
        user_id=user.id,
        name=job_data.name,
        onedrive_account_id=job_data.onedrive_account_id,
        gdrive_account_id=job_data.gdrive_account_id,
        onedrive_folder=job_data.onedrive_folder,
        gdrive_folder=job_data.gdrive_folder,
        direction=job_data.direction,
        enabled=True
    )
    
    db.add(sync_job)
    db.commit()
    db.refresh(sync_job)
    
    return sync_job


@router.get("/", response_model=List[SyncJobResponse])
async def list_sync_jobs(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all sync jobs for current user"""
    jobs = db.query(SyncJob).filter(SyncJob.user_id == user.id).all()
    return jobs


@router.get("/{job_id}", response_model=SyncJobResponse)
async def get_sync_job(
    job_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sync job details"""
    job = db.query(SyncJob).filter(
        SyncJob.id == job_id,
        SyncJob.user_id == user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sync job not found"
        )
    
    return job


@router.put("/{job_id}", response_model=SyncJobResponse)
async def update_sync_job(
    job_id: int,
    job_data: SyncJobUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update sync job"""
    job = db.query(SyncJob).filter(
        SyncJob.id == job_id,
        SyncJob.user_id == user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sync job not found"
        )
    
    # Update fields
    if job_data.name is not None:
        job.name = job_data.name
    if job_data.onedrive_folder is not None:
        job.onedrive_folder = job_data.onedrive_folder
    if job_data.gdrive_folder is not None:
        job.gdrive_folder = job_data.gdrive_folder
    if job_data.direction is not None:
        job.direction = job_data.direction
    if job_data.enabled is not None:
        job.enabled = job_data.enabled
    
    db.commit()
    db.refresh(job)
    
    return job


@router.delete("/{job_id}")
async def delete_sync_job(
    job_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete sync job"""
    job = db.query(SyncJob).filter(
        SyncJob.id == job_id,
        SyncJob.user_id == user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sync job not found"
        )
    
    db.delete(job)
    db.commit()
    
    return {"message": "Sync job deleted successfully"}


@router.post("/{job_id}/trigger")
async def trigger_sync(
    job_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger sync for a job"""
    job = db.query(SyncJob).filter(
        SyncJob.id == job_id,
        SyncJob.user_id == user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sync job not found"
        )
    
    if not job.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sync job is disabled"
        )
    
    # TODO: Implement actual sync trigger
    # For now, just return success
    return {"message": "Sync triggered successfully", "job_id": job_id}
