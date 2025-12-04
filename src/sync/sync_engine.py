"""
Synchronization engine
"""

import os
import tempfile
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from src.database.models import SyncJob, ConnectedAccount, SyncHistory
from src.auth.token_manager import token_manager
from src.sync.file_operations import FileOperations
from src.api.websocket import send_sync_status
import asyncio


class SyncEngine:
    """Main synchronization engine"""
    
    def __init__(self, db: Session):
        self.db = db
        self.file_ops = FileOperations()
        self.temp_dir = tempfile.mkdtemp(prefix="sync_")
    
    async def sync_job(self, job_id: int):
        """Execute synchronization for a job"""
        job = self.db.query(SyncJob).filter(SyncJob.id == job_id).first()
        
        if not job or not job.enabled:
            return
        
        # Create sync history
        history = SyncHistory(
            sync_job_id=job.id,
            status='in_progress',
            started_at=datetime.utcnow()
        )
        self.db.add(history)
        self.db.commit()
        
        try:
            # Send status update
            await send_sync_status(
                job.user_id,
                job.id,
                'in_progress',
                {'message': 'Starting sync...'}
            )
            
            # Get accounts
            onedrive_account = self.db.query(ConnectedAccount).filter(
                ConnectedAccount.id == job.onedrive_account_id
            ).first()
            
            gdrive_account = self.db.query(ConnectedAccount).filter(
                ConnectedAccount.id == job.gdrive_account_id
            ).first()
            
            if not onedrive_account or not gdrive_account:
                raise Exception("Accounts not found")
            
            # Get tokens
            onedrive_token = token_manager.decrypt_token(onedrive_account.access_token_encrypted)
            gdrive_token = token_manager.decrypt_token(gdrive_account.access_token_encrypted)
            
            files_synced = 0
            bytes_transferred = 0
            
            # Sync based on direction
            if job.direction in ['bidirectional', 'onedrive_to_gdrive']:
                result = await self._sync_onedrive_to_gdrive(
                    onedrive_token,
                    gdrive_token,
                    job.onedrive_folder,
                    job.gdrive_folder,
                    job.user_id,
                    job.id
                )
                files_synced += result['files']
                bytes_transferred += result['bytes']
            
            if job.direction in ['bidirectional', 'gdrive_to_onedrive']:
                result = await self._sync_gdrive_to_onedrive(
                    gdrive_token,
                    onedrive_token,
                    job.gdrive_folder,
                    job.onedrive_folder,
                    job.user_id,
                    job.id
                )
                files_synced += result['files']
                bytes_transferred += result['bytes']
            
            # Update history
            history.status = 'success'
            history.files_synced = files_synced
            history.bytes_transferred = bytes_transferred
            history.completed_at = datetime.utcnow()
            
            # Update job
            job.last_sync = datetime.utcnow()
            
            self.db.commit()
            
            # Send completion status
            await send_sync_status(
                job.user_id,
                job.id,
                'completed',
                {
                    'files_synced': files_synced,
                    'bytes_transferred': bytes_transferred
                }
            )
            
        except Exception as e:
            history.status = 'failed'
            history.error_message = str(e)
            history.completed_at = datetime.utcnow()
            self.db.commit()
            
            await send_sync_status(
                job.user_id,
                job.id,
                'failed',
                {'error': str(e)}
            )
            
            raise
    
    async def _sync_onedrive_to_gdrive(
        self,
        onedrive_token: str,
        gdrive_token: str,
        onedrive_folder: str,
        gdrive_folder_id: str,
        user_id: int,
        job_id: int
    ) -> dict:
        """Sync files from OneDrive to Google Drive"""
        
        # TODO: Implement full directory sync
        # For now, this is a placeholder that demonstrates the flow
        
        files_synced = 0
        bytes_transferred = 0
        
        # This would iterate through OneDrive files and sync them
        # Example flow for a single file:
        # 1. Download from OneDrive
        # 2. Upload to Google Drive
        # 3. Clean up temp file
        
        return {
            'files': files_synced,
            'bytes': bytes_transferred
        }
    
    async def _sync_gdrive_to_onedrive(
        self,
        gdrive_token: str,
        onedrive_token: str,
        gdrive_folder_id: str,
        onedrive_folder: str,
        user_id: int,
        job_id: int
    ) -> dict:
        """Sync files from Google Drive to OneDrive"""
        
        # TODO: Implement full directory sync
        # Similar to above but in reverse direction
        
        files_synced = 0
        bytes_transferred = 0
        
        return {
            'files': files_synced,
            'bytes': bytes_transferred
        }
    
    def cleanup(self):
        """Clean up temporary files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
