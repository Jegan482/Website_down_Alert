# app/auth/jwt_utils.py

import os
from datetime import datetime, timedelta
from jose import jwt

# Real project la .env la vachchikalam
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_THIS_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """user_id madhiri payload vaangi JWT token create pannum."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
