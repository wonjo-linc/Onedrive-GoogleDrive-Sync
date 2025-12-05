"""
FastAPI main application
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware
from src.database.session import init_db, get_db
from src.api.routes import auth, accounts, sync_jobs, folders, debug
from src.api.websocket import manager
from src.database.models import User
from sqlalchemy.orm import Session
import os

# Create FastAPI app
app = FastAPI(
    title="OneDrive-GoogleDrive Sync API",
    description="Real-time synchronization between OneDrive and Google Drive",
    version="1.0.0"
)

# Session middleware (must be before CORS)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "your-secret-key-here"),
    max_age=86400 * 7  # 7 days
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sync.lincsolution.net", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = "/app/static"
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

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
    """Serve dashboard"""
    index_path = "/app/static/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "OneDrive-GoogleDrive Sync API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    
    # Accept connection first
    await websocket.accept()
    
    try:
        # Get session cookie from websocket
        cookies = websocket.cookies
        session_cookie = cookies.get("session")
        
        if not session_cookie:
            await websocket.send_json({"type": "error", "message": "Not authenticated"})
            await websocket.close(code=1008)
            return
        
        # For now, accept all connections with session
        # In production, you should verify the session properly
        user_id = "default"  # This should be extracted from session
        
        # Connect
        await manager.connect(websocket, user_id)
        
        while True:
            # Keep connection alive and receive messages
            data = await websocket.receive_text()
            # Echo back for now (can be used for ping/pong)
            await websocket.send_json({"type": "pong", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
