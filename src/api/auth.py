"""Access control for the web UI and API. Mode comes from AUTH_MODE: 'none' (default) or 'basic'.

none  : no login. Safe only because every published port is bound to 127.0.0.1 (scripts/check_bindings.py
        refuses to start the stack otherwise).
basic : HTTP Basic with WEB_USER / WEB_PASSWORD from .env, compared in constant time.
"""
import hmac
import os

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

MODES = ("none", "basic")
security = HTTPBasic(auto_error=False)


def auth_mode() -> str:
    mode = os.environ.get("AUTH_MODE", "none")
    if mode not in MODES:
        raise RuntimeError(f"AUTH_MODE must be one of {MODES}, got {mode!r}")
    return mode


def require_auth(creds: HTTPBasicCredentials | None = Depends(security)) -> str:
    if auth_mode() == "none":
        return "anonymous"
    if creds is None:
        raise HTTPException(401, "login required", headers={"WWW-Authenticate": "Basic"})
    ok_user = hmac.compare_digest(creds.username.encode(), os.environ["WEB_USER"].encode())
    ok_pass = hmac.compare_digest(creds.password.encode(), os.environ["WEB_PASSWORD"].encode())
    if not (ok_user and ok_pass):
        raise HTTPException(401, "bad credentials", headers={"WWW-Authenticate": "Basic"})
    return creds.username
