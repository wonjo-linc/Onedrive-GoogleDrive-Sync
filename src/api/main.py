"""
FastAPI main application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database.session import init_db
from src.api.routes import auth, accounts

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
