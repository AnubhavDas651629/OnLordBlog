from datetime import UTC, datetime, timedelta
import jwt
from fastapi.security import OAuth2PasswordBearer, oauth2
from pwdlib import PasswordHash

from config import settings

password_hash = PasswordHash.recommended() #creates password hasher using argon 2 with recommended settings

# OAuth2PasswordBearer extracts the token from the authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/token") # the tokenUrl has to match our login endpoint path

# fn takes a plain text and returns it's hash
def hash_password(password: str) -> str:
    return password_hash.hash(password)

# fn verifies password
def verify_password(plain_password: str, hashed_password:str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


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