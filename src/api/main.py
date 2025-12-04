"""
FastAPI main application
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from src.database.session import init_db, get_db
from src.api.routes import auth, accounts, sync_jobs, folders, debug
from src.api.websocket import manager
from src.auth.jwt_manager import jwt_manager
from src.database.models import User
from sqlalchemy.orm import Session

# Create FastAPI app
app = FastAPI(
    title="OneDrive-GoogleDrive Sync API",
    description="Real-time synchronization between OneDrive and Google Drive",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sync.lincsolution.net", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(sync_jobs.router)
app.include_router(folders.router)
app.include_router(debug.router)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()


@app.get("/")
async def root():
    return {"message": "OneDrive-GoogleDrive Sync API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """WebSocket endpoint for real-time updates"""
    
    # Verify token
    payload = jwt_manager.verify_token(token)
    if not payload:
        await websocket.close(code=1008)  # Policy violation
        return
    
    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=1008)
        return
    
    # Connect
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Keep connection alive and receive messages
            data = await websocket.receive_text()
            # Echo back for now (can be used for ping/pong)
            await websocket.send_json({"type": "pong", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
