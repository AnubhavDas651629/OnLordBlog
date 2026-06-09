from datetime import UTC, datetime, timedelta
from unittest import result
import jwt
from fastapi.security import OAuth2PasswordBearer, oauth2
from pwdlib import PasswordHash

from config import settings

from typing import Annotated
from fastapi import Depends, HTTPException, status
from sqlalchemy import select 
from sqlalchemy.ext.asyncio import AsyncSession
import models
from config import settings
from database import get_db

import hashlib
import secrets 


password_hash = PasswordHash.recommended() #creates password hasher using argon 2 with recommended settings

# OAuth2PasswordBearer extracts the token from the authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/token") # the tokenUrl has to match our login endpoint path

# fn takes a plain text and returns it's hash
def hash_password(password: str) -> str:
    return password_hash.hash(password)

# fn verifies password
def verify_password(plain_password: str, hashed_password:str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def generate_reset_tokens() -> str:
    return secrets.token_urlsafe(32) # this function produces urlsafe base 64 characters perfect for emails

def hash_reset_token(token:str) -> str:
    return hashlib.sha256(token.encode()).hexdigest  # takes a token and returns its sha256 hash


#creates a copy a data, adds an expiration time and encodes them as json web tokens
# basically creating an access token
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """ Create a JWT token"""
    to_encode = data.copy() 
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.access_token_expire_minutes,
        )
    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )
    return encoded_jwt


# takes a token string and returns a user ID if the token is valid
# jwt -> json web token
# jwt has a header(which contains the algorithm and type), a payload(which contains our data and expiration), and a signature(which proves that a token wasn't tampered with)
def verify_access_token(token: str) -> str | None:
    """verify a JWT token and return the subject (user id) if valid"""
    try:
        payload = jwt.decode(
            token, 
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
            options={"require":["exp", "sub"]}
            )
    except jwt.InvalidTokenError:
        return None
    else:
        return payload.get("sub")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> models.User:
    user_id = verify_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid or expired token",
            headers ={"WWWW-Authenticated": "Bearer"},
        )
        
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers = {"WWW-Authenticated": "Bearer"},
        )

    result = await db.execute(
        select(models.User).where(models.User.id == user_id_int),
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail= " User not found",
            headers={"WWW-Authenticated": "bearer"},
        )
    return user

CurrentUser = Annotated[models.User, Depends(get_current_user)] # code basically saying that what we have here is a user object, and second part says that here is some meta data about the user

