"""
Token encryption and management
"""

from cryptography.fernet import Fernet
import os
import base64


class TokenManager:
    """Encrypt and decrypt OAuth tokens"""
    
    def __init__(self):
        # Get encryption key from environment or generate one
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            # Generate a new key (should be stored in .env)
            key = Fernet.generate_key().decode()
            print(f"Generated new encryption key: {key}")
            print("Add this to your .env file as ENCRYPTION_KEY")
        
        if isinstance(key, str):
            key = key.encode()
        
        self.cipher = Fernet(key)
    
    def encrypt_token(self, token: str) -> str:
        """Encrypt a token"""
        if not token:
            return None
        encrypted = self.cipher.encrypt(token.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt a token"""
        if not encrypted_token:
            return None
        try:
            decoded = base64.b64decode(encrypted_token.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            print(f"Token decryption failed: {e}")
            return None


# Global instance
token_manager = TokenManager()
