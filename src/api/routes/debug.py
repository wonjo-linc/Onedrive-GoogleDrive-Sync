"""
Debug routes for troubleshooting
"""

from fastapi import APIRouter
import os
from src.auth.jwt_manager import jwt_manager

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


@router.get("/verify-token/{token}")
async def verify_token_debug(token: str):
    """Verify a JWT token (for debugging)"""
    payload = jwt_manager.verify_token(token)
    return {
        "valid": payload is not None,
        "payload": payload
    }
