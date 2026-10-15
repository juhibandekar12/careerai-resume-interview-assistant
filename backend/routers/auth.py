"""
backend/routers/auth.py
-----------------------
Authentication endpoints: register, login, get profile.
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, EmailStr, Field
from utils.auth import register_user, authenticate_user, verify_token, get_user_by_id

router = APIRouter()


# ── Pydantic schemas ───────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username:  str = Field(..., min_length=3, max_length=30)
    email:     EmailStr
    password:  str = Field(..., min_length=6)
    full_name: str = Field(default="")


class LoginRequest(BaseModel):
    username: str
    password: str


# ── Helper ─────────────────────────────────────────────────────────────────────

def _get_user_from_token(authorization: str | None) -> dict:
    """Extract and verify bearer token; raise 401 on failure."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token.")
    token = authorization.split(" ", 1)[1]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token expired or invalid.")
    return payload


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/register", summary="Register a new user")
def register(req: RegisterRequest):
    try:
        user = register_user(req.username, req.email, req.password, req.full_name)
        return {"success": True, "user": user}
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/login", summary="Authenticate and receive a token")
def login(req: LoginRequest):
    result = authenticate_user(req.username, req.password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    return {"success": True, "data": result}


@router.get("/profile", summary="Get current user profile")
def get_profile(authorization: str | None = Header(default=None)):
    payload = _get_user_from_token(authorization)
    user = get_user_by_id(payload["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"success": True, "data": user}
