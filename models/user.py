"""
models/user.py
--------------
Pydantic models for user-related data transfer.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    username:  str        = Field(..., min_length=3, max_length=30)
    email:     EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(UserBase):
    id:         int
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserWithToken(UserOut):
    token: str


class TokenPayload(BaseModel):
    user_id:  int
    username: str
    exp:      int
