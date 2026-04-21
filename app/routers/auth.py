"""Authentication: Google and Apple OAuth2 + JWT tokens.

Anonymous-first: all read endpoints work without auth. Auth is optional
and adds sync/persistence features. The frontend stores the JWT in an
httpOnly cookie and sends it automatically.

Environment variables required:
  GOOGLE_CLIENT_ID      — from Google Cloud Console
  GOOGLE_CLIENT_SECRET  — from Google Cloud Console
  APPLE_CLIENT_ID       — from Apple Developer Portal (Services ID)
  APPLE_TEAM_ID         — from Apple Developer Portal
  APPLE_KEY_ID          — from Apple Developer Portal
  APPLE_PRIVATE_KEY     — contents of .p8 key file (newlines as \\n)
  AUTH_SECRET_KEY        — random 32+ char string for JWT signing
  AUTH_FRONTEND_URL      — e.g. http://localhost:5174
"""

import json
import os
import time
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, HTTPException, Query, Request, Response, Depends
from fastapi.responses import RedirectResponse
from jose import jwt, JWTError
from pydantic import BaseModel
from sqlalchemy import text

from pipeline.db import engine

router = APIRouter(tags=["auth"])

# Config from environment
SECRET_KEY = os.environ.get("AUTH_SECRET_KEY", "dev-secret-key-change-in-production-32chars!")
ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 30
FRONTEND_URL = os.environ.get("AUTH_FRONTEND_URL", "http://localhost:5174")

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8001/api/v1/auth/google/callback")

APPLE_CLIENT_ID = os.environ.get("APPLE_CLIENT_ID", "")
APPLE_TEAM_ID = os.environ.get("APPLE_TEAM_ID", "")
APPLE_KEY_ID = os.environ.get("APPLE_KEY_ID", "")
APPLE_PRIVATE_KEY = os.environ.get("APPLE_PRIVATE_KEY", "").replace("\\n", "\n")
APPLE_REDIRECT_URI = os.environ.get("APPLE_REDIRECT_URI", "http://localhost:8001/api/v1/auth/apple/callback")


def create_token(user_id: str, email: str, display_name: str, avatar_url: str = "",
                  username: str = "", is_new: bool = False) -> str:
    """Create a JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "email": email,
        "name": display_name,
        "avatar": avatar_url,
        "username": username,
        "is_new": is_new,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(request: Request) -> dict | None:
    """Extract user from JWT cookie. Returns None if not logged in (anonymous OK)."""
    token = request.cookies.get("rs_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name"),
            "avatar": payload.get("avatar"),
            "username": payload.get("username", ""),
            "is_new": payload.get("is_new", False),
        }
    except JWTError:
        return None


def get_optional_user(request: Request) -> dict | None:
    """Dependency: returns user dict or None. Never raises."""
    return get_current_user(request)


def upsert_user(provider: str, provider_id: str, email: str, display_name: str, avatar_url: str = "") -> dict:
    """Create or update user record, return user dict."""
    with engine.connect() as conn:
        # Try to find existing user
        row = conn.execute(text("""
            SELECT id, email, display_name, avatar_url, username, is_new FROM users
            WHERE provider = :provider AND provider_id = :pid
        """), {"provider": provider, "pid": provider_id}).fetchone()

        if row:
            # Existing user — update last login and profile info, mark as not new
            conn.execute(text("""
                UPDATE users SET last_login_at = now(), display_name = :name,
                    avatar_url = :avatar, email = :email, is_new = false
                WHERE id = :id
            """), {"id": row[0], "name": display_name, "avatar": avatar_url, "email": email})
            conn.commit()
            return {"id": str(row[0]), "email": email, "name": display_name,
                    "avatar": avatar_url, "username": row[4] or "", "is_new": False}
        else:
            # New user — is_new=true until they set a username
            new_row = conn.execute(text("""
                INSERT INTO users (email, display_name, avatar_url, provider, provider_id, is_new)
                VALUES (:email, :name, :avatar, :provider, :pid, true)
                RETURNING id
            """), {"email": email, "name": display_name, "avatar": avatar_url,
                   "provider": provider, "pid": provider_id}).fetchone()
            conn.commit()
            return {"id": str(new_row[0]), "email": email, "name": display_name,
                    "avatar": avatar_url, "username": "", "is_new": True}


def set_auth_cookie(response: Response, token: str):
    """Set JWT as httpOnly cookie."""
    response.set_cookie(
        key="rs_token",
        value=token,
        httponly=True,
        secure=False,  # Set True in production with HTTPS
        samesite="lax",
        max_age=TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )


# ═══════════════════════════════════════
# Google OAuth2
# ═══════════════════════════════════════

@router.get("/auth/google/login")
def google_login():
    """Redirect to Google OAuth2 consent screen."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(503, "Google OAuth not configured. Set GOOGLE_CLIENT_ID.")

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(url)


@router.get("/auth/google/callback")
def google_callback(code: str, response: Response):
    """Handle Google OAuth2 callback."""
    # Exchange code for tokens
    token_resp = httpx.post("https://oauth2.googleapis.com/token", data={
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    })
    if token_resp.status_code != 200:
        raise HTTPException(400, "Failed to exchange Google auth code")

    tokens = token_resp.json()
    id_token = tokens.get("id_token")
    if not id_token:
        raise HTTPException(400, "No ID token from Google")

    # Decode ID token (Google tokens are JWTs — we verify via Google's certs)
    # For simplicity, use the userinfo endpoint instead
    userinfo_resp = httpx.get("https://www.googleapis.com/oauth2/v3/userinfo", headers={
        "Authorization": f"Bearer {tokens['access_token']}",
    })
    if userinfo_resp.status_code != 200:
        raise HTTPException(400, "Failed to get Google user info")

    info = userinfo_resp.json()
    user = upsert_user(
        provider="google",
        provider_id=info["sub"],
        email=info.get("email", ""),
        display_name=info.get("name", info.get("email", "User")),
        avatar_url=info.get("picture", ""),
    )

    token = create_token(user["id"], user["email"], user["name"], user["avatar"],
                         user.get("username", ""), user.get("is_new", False))
    redirect = RedirectResponse(f"{FRONTEND_URL}/auth/success", status_code=302)
    set_auth_cookie(redirect, token)
    return redirect


# ═══════════════════════════════════════
# Apple Sign In
# ═══════════════════════════════════════

def _apple_client_secret() -> str:
    """Generate Apple client secret JWT (valid for 6 months)."""
    now = int(time.time())
    headers = {"kid": APPLE_KEY_ID, "alg": "ES256"}
    payload = {
        "iss": APPLE_TEAM_ID,
        "iat": now,
        "exp": now + 86400 * 180,
        "aud": "https://appleid.apple.com",
        "sub": APPLE_CLIENT_ID,
    }
    return jwt.encode(payload, APPLE_PRIVATE_KEY, algorithm="ES256", headers=headers)


@router.get("/auth/apple/login")
def apple_login():
    """Redirect to Apple Sign In."""
    if not APPLE_CLIENT_ID:
        raise HTTPException(503, "Apple Sign In not configured. Set APPLE_CLIENT_ID.")

    params = {
        "client_id": APPLE_CLIENT_ID,
        "redirect_uri": APPLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "name email",
        "response_mode": "form_post",
    }
    url = "https://appleid.apple.com/auth/authorize?" + "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(url)


@router.post("/auth/apple/callback")
def apple_callback(request: Request, response: Response):
    """Handle Apple Sign In callback (form_post)."""
    import asyncio
    # Apple sends POST with form data
    # We need to read the form — use sync approach
    # Note: In production, use async endpoint
    raise HTTPException(501, "Apple callback requires async form parsing — see /auth/apple/callback-async")


@router.post("/auth/apple/callback-async")
async def apple_callback_async(request: Request):
    """Handle Apple Sign In callback (async for form parsing)."""
    form = await request.form()
    code = form.get("code")
    if not code:
        raise HTTPException(400, "No authorization code from Apple")

    # Exchange code for tokens
    client_secret = _apple_client_secret()
    token_resp = httpx.post("https://appleid.apple.com/auth/token", data={
        "code": code,
        "client_id": APPLE_CLIENT_ID,
        "client_secret": client_secret,
        "redirect_uri": APPLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    })
    if token_resp.status_code != 200:
        raise HTTPException(400, "Failed to exchange Apple auth code")

    tokens = token_resp.json()
    id_token_str = tokens.get("id_token")
    if not id_token_str:
        raise HTTPException(400, "No ID token from Apple")

    # Decode Apple ID token (unverified — in production, verify with Apple's public keys)
    claims = jwt.get_unverified_claims(id_token_str)

    # Apple only sends name on first login — it comes in the form data
    user_data = form.get("user")
    name = ""
    if user_data:
        import json
        try:
            user_json = json.loads(user_data)
            first = user_json.get("name", {}).get("firstName", "")
            last = user_json.get("name", {}).get("lastName", "")
            name = f"{first} {last}".strip()
        except Exception:
            pass

    email = claims.get("email", "")
    apple_sub = claims.get("sub", "")

    user = upsert_user(
        provider="apple",
        provider_id=apple_sub,
        email=email,
        display_name=name or email.split("@")[0] or "Apple User",
    )

    token = create_token(user["id"], user["email"], user["name"], user["avatar"],
                         user.get("username", ""), user.get("is_new", False))
    redirect = RedirectResponse(f"{FRONTEND_URL}/auth/success", status_code=302)
    set_auth_cookie(redirect, token)
    return redirect


# ═══════════════════════════════════════
# Session management
# ═══════════════════════════════════════

@router.get("/auth/me")
def get_me(request: Request):
    """Return current user info, or null if anonymous."""
    user = get_current_user(request)
    if not user:
        return {"user": None, "anonymous": True}

    # Refresh username/is_new from DB (JWT may be stale)
    with engine.connect() as conn:
        row = conn.execute(text(
            "SELECT username, is_new FROM users WHERE id = :uid"
        ), {"uid": user["id"]}).fetchone()
        if row:
            user["username"] = row[0] or ""
            user["is_new"] = bool(row[1])
            user["needs_username"] = not row[0]

    return {"user": user, "anonymous": False}


@router.post("/auth/logout")
def logout(response: Response):
    """Clear auth cookie."""
    response.delete_cookie("rs_token", path="/")
    return {"message": "Logged out"}


class MigrateRequest(BaseModel):
    anonymous_id: str  # localStorage key used for anonymous data
    observation_ids: list[str] = []  # anonymous observation IDs to claim
    saved_items: list[dict] = []  # saved items to persist server-side


@router.post("/auth/migrate")
def migrate_anonymous_data(body: MigrateRequest, request: Request):
    """After login, migrate anonymous localStorage data to the user's account.

    Links anonymous observations to the user and optionally stores saved items.
    """
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Must be logged in to migrate data")

    user_id = user["id"]
    migrated = 0

    with engine.connect() as conn:
        # Link anonymous observations to user
        for obs_id in body.observation_ids:
            result = conn.execute(text("""
                UPDATE user_observations SET user_id = :uid
                WHERE id = :oid AND user_id IS NULL
            """), {"uid": user_id, "oid": obs_id})
            migrated += result.rowcount

        # Store anonymous_id for future linking
        conn.execute(text("""
            UPDATE users SET anonymous_id = :anon WHERE id = :uid
        """), {"uid": user_id, "anon": body.anonymous_id})

        conn.commit()

    return {"migrated_observations": migrated, "user_id": user_id}


# ═══════════════════════════════════════
# Username setup (required after first OAuth)
# ═══════════════════════════════════════

class UsernameRequest(BaseModel):
    username: str


@router.post("/auth/username")
def set_username(body: UsernameRequest, request: Request, response: Response):
    """Set username after first OAuth signup. Must be unique, no spaces, 3-30 chars."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Must be logged in")

    username = body.username.strip().lower()

    # Validate format
    import re
    if not re.match(r'^[a-z0-9_]{3,30}$', username):
        raise HTTPException(400, "Username must be 3-30 characters: letters, numbers, underscores only")

    # Check uniqueness
    with engine.connect() as conn:
        existing = conn.execute(text(
            "SELECT id FROM users WHERE username = :u AND id != :uid"
        ), {"u": username, "uid": user["id"]}).fetchone()
        if existing:
            raise HTTPException(409, "Username already taken")

        conn.execute(text("""
            UPDATE users SET username = :u, is_new = false WHERE id = :uid
        """), {"u": username, "uid": user["id"]})
        conn.commit()

    # Issue new token with username
    new_token = create_token(user["id"], user["email"], user["name"], user["avatar"],
                             username, False)
    set_auth_cookie(response, new_token)

    return {"username": username, "message": "Username set"}


@router.get("/auth/username/check")
def check_username(username: str = Query(..., min_length=3, max_length=30)):
    """Check if a username is available."""
    import re
    clean = username.strip().lower()
    if not re.match(r'^[a-z0-9_]{3,30}$', clean):
        return {"available": False, "reason": "Letters, numbers, and underscores only (3-30 chars)"}

    with engine.connect() as conn:
        existing = conn.execute(text(
            "SELECT id FROM users WHERE username = :u"
        ), {"u": clean}).fetchone()

    return {"available": not existing, "username": clean}


# ═══════════════════════════════════════
# User settings (card config, preferences)
# ═══════════════════════════════════════

@router.get("/auth/settings")
def get_settings(request: Request):
    """Get user's saved settings (card configs, preferences)."""
    user = get_current_user(request)
    if not user:
        return {"settings": {}}

    with engine.connect() as conn:
        row = conn.execute(text(
            "SELECT settings FROM user_settings WHERE user_id = :uid"
        ), {"uid": user["id"]}).fetchone()

    return {"settings": row[0] if row else {}}


@router.put("/auth/settings")
def save_settings(body: dict, request: Request):
    """Save user settings. Merges with existing settings."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Must be logged in to save settings")

    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO user_settings (user_id, settings, updated_at)
            VALUES (:uid, :settings, now())
            ON CONFLICT (user_id) DO UPDATE SET
                settings = user_settings.settings || :settings,
                updated_at = now()
        """), {"uid": user["id"], "settings": json.dumps(body)})
        conn.commit()

    return {"message": "Settings saved"}
