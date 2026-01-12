from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import HTTPException, Depends, status, APIRouter, Cookie
from typing import Optional
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security = HTTPBearer(auto_error=False)

# функция генерации токена
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# функция проверки токена и роли администратора
def get_current_admin(access_token: Optional[str] = Cookie(None)) -> dict:
    """Получить текущего админа из cookie"""
    
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    exp = payload.get("exp")
    if exp is None or datetime.utcnow() > datetime.utcfromtimestamp(exp):
        raise HTTPException(status_code=403, detail="Token has expired")
    
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not enough privileges")
    
    return {
        "user_id": payload.get("user_id"),
        "email": payload.get("email"),
        "role": payload.get("role")
    }

def get_current_user(access_token: Optional[str] = Cookie(None)) -> Optional[dict]:
    """Получить текущего пользователя из cookie"""
    
    if not access_token:
        return None
    
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
    
    exp = payload.get("exp")
    if exp is None or datetime.utcnow() > datetime.utcfromtimestamp(exp):
        return None
    
    return {
        "user_id": payload.get("user_id"),
        "email": payload.get("email"),
        "role": payload.get("role")
    }

ADMIN_DATA = {
    "email": "admin@example.com",
    "password": "admin123",
    "role": "admin",
    "user_id": 1
}

USERS_DATA = {
    "user1@example.com": {
        "password": "password123",
        "role": "user",
        "user_id": 2
    },
    "user2@example.com": {
        "password": "pass456",
        "role": "user",
        "user_id": 3
    }
}

@router.post("/login")
def login(data: LoginRequest):
    if data.email == ADMIN_DATA["email"] and data.password == ADMIN_DATA["password"]:
        user_data = ADMIN_DATA
    elif data.email in USERS_DATA and USERS_DATA[data.email]["password"] == data.password:
        user_data = USERS_DATA[data.email]
        user_data["email"] = data.email
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        {
            "user_id": user_data["user_id"],
            "email": data.email,
            "role": user_data["role"]
        }
    )
    return {
        "access_token": token,
        "token_type": "bearer"
    }