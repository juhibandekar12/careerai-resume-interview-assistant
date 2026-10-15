"""
utils/auth.py
-------------
User authentication utilities: password hashing, JWT token creation/verification.
"""

import hashlib
import hmac
import os
import time
import base64
import json
import logging
from database.db import fetchone, execute

logger = logging.getLogger(__name__)

# Secret key – in production load from env variable
SECRET_KEY = os.environ.get("SECRET_KEY", "career_assist_super_secret_2024")


# ──────────────────────────────────────────────────────────────────────────────
# Password helpers
# ──────────────────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Return a salted SHA-256 hash of the password."""
    salt = os.urandom(16).hex()
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a plain-text password against a stored salted hash."""
    try:
        salt, hashed = stored_hash.split(":", 1)
        expected = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
        return hmac.compare_digest(expected, hashed)
    except ValueError:
        return False


# ──────────────────────────────────────────────────────────────────────────────
# Simple JWT-like token (base64 payload + HMAC signature)
# ──────────────────────────────────────────────────────────────────────────────

def create_token(user_id: int, username: str, expires_in: int = 86400) -> str:
    """
    Create a signed token containing user_id, username, and expiry.
    Format: base64(payload).signature
    """
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": int(time.time()) + expires_in
    }
    payload_b64 = base64.urlsafe_b64encode(
        json.dumps(payload).encode()
    ).decode()
    signature = hmac.new(
        SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256
    ).hexdigest()
    return f"{payload_b64}.{signature}"


def verify_token(token: str) -> dict | None:
    """
    Verify a token and return the payload dict, or None if invalid/expired.
    """
    try:
        payload_b64, signature = token.rsplit(".", 1)
        expected_sig = hmac.new(
            SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected_sig, signature):
            return None
        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode())
        if payload.get("exp", 0) < int(time.time()):
            return None
        return payload
    except Exception as exc:
        logger.warning("Token verification failed: %s", exc)
        return None


# ──────────────────────────────────────────────────────────────────────────────
# User CRUD
# ──────────────────────────────────────────────────────────────────────────────

def register_user(username: str, email: str, password: str, full_name: str = "") -> dict:
    """Register a new user. Raises ValueError on duplicate username/email."""
    existing = fetchone(
        "SELECT id FROM users WHERE username=? OR email=?", (username, email)
    )
    if existing:
        raise ValueError("Username or email already exists.")

    pw_hash = hash_password(password)
    user_id = execute(
        "INSERT INTO users (username, email, password_hash, full_name) VALUES (?,?,?,?)",
        (username, email, pw_hash, full_name)
    )
    return {"user_id": user_id, "username": username, "email": email}


def authenticate_user(username: str, password: str) -> dict | None:
    """Return user dict + token if credentials are valid, else None."""
    user = fetchone(
        "SELECT id, username, email, full_name, password_hash FROM users WHERE username=?",
        (username,)
    )
    if not user or not verify_password(password, user["password_hash"]):
        return None

    # Update last_login
    execute("UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE id=?", (user["id"],))
    token = create_token(user["id"], user["username"])
    return {
        "user_id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "full_name": user["full_name"],
        "token": token
    }


def get_user_by_id(user_id: int) -> dict | None:
    """Fetch user profile (without password hash)."""
    return fetchone(
        "SELECT id, username, email, full_name, created_at, last_login FROM users WHERE id=?",
        (user_id,)
    )
