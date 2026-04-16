import os
from fastapi import Depends, HTTPException, Request
from auth.jwt_handler import decode_token


def _auth_enabled() -> bool:
    return os.environ.get("AUTH_ENABLED", "false").lower() == "true"


async def get_current_user(request: Request) -> dict | None:
    """Extract user from JWT. Returns None if auth disabled."""
    if not _auth_enabled():
        return {"sub": "anonymous", "role": "admin"}

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = auth_header[7:]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload


def require_role(role: str):
    """Dependency that checks user role."""
    async def check(user: dict = Depends(get_current_user)):
        if not _auth_enabled():
            return user
        if user.get("role") != role:
            raise HTTPException(status_code=403, detail=f"Requires {role} role")
        return user
    return check
