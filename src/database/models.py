"""
Database models for the sync system
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User account"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String)
    provider = Column(String, nullable=False)  # 'microsoft' or 'google'
    provider_user_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    connected_accounts = relationship("ConnectedAccount", back_populates="user", cascade="all, delete-orphan")
    sync_jobs = relationship("SyncJob", back_populates="user", cascade="all, delete-orphan")


class ConnectedAccount(Base):
    """Connected OneDrive or Google Drive account"""
    __tablename__ = "connected_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    platform = Column(String, nullable=False)  # 'onedrive' or 'gdrive'
    email = Column(String, nullable=False)
    access_token_encrypted = Column(Text)
    refresh_token_encrypted = Column(Text)
    token_expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="connected_accounts")


class SyncJob(Base):
    """Synchronization job"""
    __tablename__ = "sync_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    onedrive_account_id = Column(Integer, ForeignKey("connected_accounts.id"))
    gdrive_account_id = Column(Integer, ForeignKey("connected_accounts.id"))
    onedrive_folder = Column(String, nullable=False)
    gdrive_folder = Column(String, nullable=False)
    direction = Column(String, default="bidirectional")  # 'bidirectional', 'onedrive_to_gdrive', 'gdrive_to_onedrive'
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_sync = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="sync_jobs")
    webhook_subscriptions = relationship("WebhookSubscription", back_populates="sync_job", cascade="all, delete-orphan")
    sync_history = relationship("SyncHistory", back_populates="sync_job", cascade="all, delete-orphan")


class WebhookSubscription(Base):
    """Webhook subscription for real-time sync"""
    __tablename__ = "webhook_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    sync_job_id = Column(Integer, ForeignKey("sync_jobs.id"), nullable=False)
    platform = Column(String, nullable=False)  # 'onedrive' or 'gdrive'
    subscription_id = Column(String)
    resource_path = Column(String)
    expiration = Column(DateTime)
    
    # Relationships
    sync_job = relationship("SyncJob", back_populates="webhook_subscriptions")


class SyncHistory(Base):
    """Synchronization history"""
    __tablename__ = "sync_history"
    
    id = Column(Integer, primary_key=True, index=True)
    sync_job_id = Column(Integer, ForeignKey("sync_jobs.id"), nullable=False)
    status = Column(String, nullable=False)  # 'success', 'failed', 'in_progress'
    files_synced = Column(Integer, default=0)
    bytes_transferred = Column(Integer, default=0)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    
    # Relationships
    sync_job = relationship("SyncJob", back_populates="sync_history")
