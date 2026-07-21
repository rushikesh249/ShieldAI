"""
ShieldAI Backend — Authentication Dependency (Placeholder)

Provides a ``get_current_user`` dependency that will eventually
validate JWT tokens and return authenticated user details.

Currently returns a mock user for development purposes.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import Depends, HTTPException, Request, status

from app.utils.jwt import decode_access_token


async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Dependency: resolve and authenticate the current user via JWT access token.

    Supports both local mock-issued tokens and standard Supabase JWT access tokens.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Must be 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Standardize the user object returned to the API routes.
    # Supabase uses 'sub' for the user ID. Local development may use 'id' or 'sub'.
    user_id = payload.get("sub") or payload.get("id")
    email = payload.get("email")
    
    # Check roles. In Supabase JWTs, metadata or role claims are often custom.
    # We check: payload['user_metadata']['role'], payload['role'], then payload['role'] in local tokens.
    role = "analyst"
    if "user_metadata" in payload and isinstance(payload["user_metadata"], dict):
        role = payload["user_metadata"].get("role", role)
    elif "role" in payload:
        role = payload["role"]

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing user identifiers",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "id": user_id,
        "email": email,
        "role": role,
        "name": payload.get("name", email.split("@")[0] if email else "User"),
    }

