from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from auth.jwt_handler import create_token

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# Hardcoded demo credentials
DEMO_USERS = {
    "rider": {"password": "rider123", "role": "rider", "name": "Ravi Kumar"},
    "admin": {"password": "admin123", "role": "admin", "name": "Admin User"},
}


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    role: str
    name: str


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest):
    """Login with demo credentials."""
    user = DEMO_USERS.get(payload.username)
    if not user or user["password"] != payload.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(user_id=payload.username, role=user["role"])
    return LoginResponse(token=token, role=user["role"], name=user["name"])
