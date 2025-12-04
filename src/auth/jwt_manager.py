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
        # Try to read from file first, then environment variable
        secret_key_file = "/app/data/.secret_key"
        
        if os.path.exists(secret_key_file):
            with open(secret_key_file, 'r') as f:
                self.secret_key = f.read().strip()
        else:
            self.secret_key = os.getenv("SECRET_KEY")
            # Save to file for persistence
            if self.secret_key:
                os.makedirs(os.path.dirname(secret_key_file), exist_ok=True)
                with open(secret_key_file, 'w') as f:
                    f.write(self.secret_key)
        
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
        except JWTError as e:
            print(f"JWT verification failed: {e}")
            return None


# Global instance
jwt_manager = JWTManager()
