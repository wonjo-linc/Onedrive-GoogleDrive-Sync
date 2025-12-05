"""
Debug routes for troubleshooting
"""

from fastapi import APIRouter, Request
import os

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/env")
async def check_environment():
    """Check environment variables (for debugging)"""
    return {
        "SECRET_KEY_length": len(os.getenv("SECRET_KEY", "")),
        "SECRET_KEY_first_10": os.getenv("SECRET_KEY", "")[:10],
        "AZURE_CLIENT_ID_set": bool(os.getenv("AZURE_CLIENT_ID")),
        "GOOGLE_CLIENT_ID_set": bool(os.getenv("GOOGLE_CLIENT_ID")),
        "DATABASE_URL": os.getenv("DATABASE_URL")
    }


@router.get("/session")
async def check_session(request: Request):
    """Check current session (for debugging)"""
    return {
        "has_session": "session" in request.cookies,
        "user_id": request.session.get("user_id"),
        "session_keys": list(request.session.keys())
    }
