"""HTTP Basic auth for the web UI and API. Credentials come from .env (WEB_USER / WEB_PASSWORD)."""
import hmac
import os

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()


def require_auth(creds: HTTPBasicCredentials = Depends(security)) -> str:
    ok_user = hmac.compare_digest(creds.username.encode(), os.environ["WEB_USER"].encode())
    ok_pass = hmac.compare_digest(creds.password.encode(), os.environ["WEB_PASSWORD"].encode())
    if not (ok_user and ok_pass):
        raise HTTPException(401, "bad credentials", headers={"WWW-Authenticate": "Basic"})
    return creds.username
