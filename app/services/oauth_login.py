"""Verify OAuth tokens from Google, Facebook, and Instagram (Basic Display)."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.config import settings

logger = logging.getLogger(__name__)


def _google_client_ids() -> list[str]:
    raw = (settings.GOOGLE_OAUTH_CLIENT_ID or "").strip()
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def verify_google_id_token(token: str) -> dict[str, Any]:
    ids = _google_client_ids()
    if not ids:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in is not configured",
        )
    info: dict | None = None
    try:
        for aud in ids:
            try:
                info = google_id_token.verify_oauth2_token(
                    token, google_requests.Request(), audience=aud
                )
                break
            except ValueError:
                continue
        if info is None:
            raise ValueError("Invalid Google token audience")
    except ValueError as e:
        logger.warning("Google token verify failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        ) from e

    email = info.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account has no email on file",
        )
    sub = info.get("sub")
    name = info.get("name") or email.split("@")[0]
    return {"provider": "google", "sub": str(sub), "email": str(email).lower(), "full_name": name}


async def verify_facebook_access_token(token: str) -> dict[str, Any]:
    if not settings.FACEBOOK_APP_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Facebook sign-in is not configured",
        )
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(
            "https://graph.facebook.com/me",
            params={"fields": "id,name,email", "access_token": token},
        )
    if r.status_code != 200:
        logger.warning("Facebook /me failed: %s %s", r.status_code, r.text)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Facebook token",
        )
    data = r.json()
    uid = str(data.get("id", ""))
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Facebook response missing id",
        )
    email = (data.get("email") or "").strip().lower()
    if not email:
        email = f"fb_{uid}@oauth.facebook.local"
    name = data.get("name") or email.split("@")[0]
    return {"provider": "facebook", "sub": uid, "email": email, "full_name": name}


async def exchange_instagram_code(code: str) -> str:
    cid = settings.INSTAGRAM_CLIENT_ID
    sec = settings.INSTAGRAM_CLIENT_SECRET
    redir = settings.INSTAGRAM_REDIRECT_URI
    if not cid or not sec or not redir:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Instagram sign-in is not fully configured (client id, secret, redirect URI)",
        )
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(
            "https://api.instagram.com/oauth/access_token",
            data={
                "client_id": cid,
                "client_secret": sec,
                "grant_type": "authorization_code",
                "redirect_uri": redir,
                "code": code,
            },
        )
    if r.status_code != 200:
        logger.warning("Instagram token exchange failed: %s %s", r.status_code, r.text)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not exchange Instagram authorization code",
        )
    body = r.json()
    access = body.get("access_token")
    if not access:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Instagram token response missing access_token",
        )
    return str(access)


async def verify_instagram_access_token(access_token: str) -> dict[str, Any]:
    if not settings.INSTAGRAM_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Instagram sign-in is not configured",
        )
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(
            "https://graph.instagram.com/me",
            params={"fields": "id,username", "access_token": access_token},
        )
    if r.status_code != 200:
        logger.warning("Instagram /me failed: %s %s", r.status_code, r.text)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Instagram token",
        )
    data = r.json()
    uid = str(data.get("id", ""))
    username = (data.get("username") or "user").strip()
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Instagram response missing id",
        )
    safe_user = "".join(c for c in username if c.isalnum() or c in "._-")[:50] or uid
    email = f"ig_{safe_user}_{uid}@oauth.instagram.local"
    return {
        "provider": "instagram",
        "sub": uid,
        "email": email.lower(),
        "full_name": username or f"Instagram user {uid}",
    }
