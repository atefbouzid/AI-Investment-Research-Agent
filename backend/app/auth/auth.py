"""
Authentication and authorization utilities
"""

import os
from jose import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from app.database.database import authenticate_user, get_user_by_id
import re

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))  # Default: 8 hours

print(f"DEBUG: JWT SECRET_KEY loaded: {SECRET_KEY[:10]}...{SECRET_KEY[-10:] if len(SECRET_KEY) > 20 else SECRET_KEY}")

# Security scheme
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password according to security requirements.
    
    Requirements:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    - Contains at least one special character
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)"
    
    return True, "Password is valid"

def validate_email(email: str) -> tuple[bool, str]:
    """
    Validate email format.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(email_pattern, email):
        return True, "Email is valid"
    return False, "Invalid email format"

def validate_username(username: str) -> tuple[bool, str]:
    """
    Validate username format.
    
    Requirements:
    - At least 3 characters long
    - No more than 50 characters
    - Only alphanumeric characters and underscores
    - Must start with a letter
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if len(username) > 50:
        return False, "Username must not exceed 50 characters"
    
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', username):
        return False, "Username must start with a letter and contain only letters, numbers, and underscores"
    
    return True, "Username is valid"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a JWT token."""
    try:
        print(f"DEBUG: Decoding token with SECRET_KEY: {SECRET_KEY[:10]}...")
        print(f"DEBUG: Token to decode: {token[:30]}...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"DEBUG: Decoded payload: {payload}")

        # Check if required fields are present
        if not payload.get("sub") or not payload.get("username"):
            print(f"DEBUG: Missing required fields. sub: {payload.get('sub')}, username: {payload.get('username')}")
            return None
        return payload
    except jwt.JWTError as e:
        print(f"DEBUG: JWT verification failed: {e}")
        print(f"DEBUG: Token was: {token}")
        print(f"DEBUG: Secret key: {SECRET_KEY}")
        return None
    except Exception as e:
        print(f"DEBUG: Token verification error: {e}")
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user."""
    token = credentials.credentials
    print(f"DEBUG: Received token: {token[:20]}...{token[-20:] if len(token) > 40 else token}")
    payload = verify_token(token)
    print(f"DEBUG: Token payload: {payload}")
    if payload is None:
        print("DEBUG: Token verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get data from token payload (consistent with token creation)
    user_id = payload.get("sub")  # This contains the user ID
    username = payload.get("username")  # This contains the username
    role = payload.get("role", "user")
    
    if not user_id or not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Return user data from token
    user = {
        "id": user_id,
        "username": username,
        "role": role,
        "is_active": True
    }
    
    return user

async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current active user."""
    if not current_user.get("is_active"):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def authenticate_and_create_token(username: str, password: str) -> Optional[str]:
    """Authenticate user and create access token."""
    user = authenticate_user(username, password)
    if user:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user["id"]), "username": user["username"], "role": user["role"]}, 
            expires_delta=access_token_expires
        )
        return access_token
    
    return None