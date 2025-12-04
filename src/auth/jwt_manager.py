"""
JWT token management
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import os


class JWTManager:
    """JWT token creation and validation"""
    
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
    
    def __init__(self):
        self.secret_key = os.getenv("SECRET_KEY")
        if not self.secret_key or len(self.secret_key) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.ALGORITHM])
            return payload
        except JWTError:
            return None


# Global instance
jwt_manager = JWTManager()
