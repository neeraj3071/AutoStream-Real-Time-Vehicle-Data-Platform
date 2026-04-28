"""Authentication module."""
import logging
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from config import Config
from models import TokenData, User

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthManager:
    """Manage authentication and JWT tokens."""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + Config.JWT_EXPIRATION_DELTA
        
        to_encode.update({"exp": expire})
        
        try:
            encoded_jwt = jwt.encode(
                to_encode,
                Config.JWT_SECRET_KEY,
                algorithm=Config.JWT_ALGORITHM
            )
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating token: {e}")
            raise
    
    @staticmethod
    def verify_token(token: str) -> Optional[TokenData]:
        """Verify JWT token and return token data."""
        try:
            payload = jwt.decode(
                token,
                Config.JWT_SECRET_KEY,
                algorithms=[Config.JWT_ALGORITHM]
            )
            username: str = payload.get("sub")
            if username is None:
                return None
            return TokenData(username=username)
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password."""
        return pwd_context.verify(plain_password, hashed_password)


# Mock user database - in production, use real database
FAKE_USERS_DB = {
    "admin": {
        "username": "admin",
        "email": "admin@example.com",
        "hashed_password": pwd_context.hash("admin123"),
        "disabled": False,
    },
    "user": {
        "username": "user",
        "email": "user@example.com",
        "hashed_password": pwd_context.hash("user123"),
        "disabled": False,
    }
}


def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user."""
    user_dict = FAKE_USERS_DB.get(username)
    if not user_dict:
        return None
    
    if not AuthManager.verify_password(password, user_dict.get("hashed_password", "")):
        return None
    
    return User(**user_dict)
