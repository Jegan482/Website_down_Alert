# app/auth/deps.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from bson import ObjectId

from app.database import db
from app.auth.jwt_utils import SECRET_KEY, ALGORITHM

# FastAPI docs-ku tokenUrl mattum use aagum; actual login form JSON dhaan
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Authorization: Bearer <token> la irukkura JWT decode panni
    user info return pannum.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise credentials_exception

    # Password etc remove panni clean object return pannrom
    return {
        "id": str(user["_id"]),
        "username": user.get("username"),
    }
