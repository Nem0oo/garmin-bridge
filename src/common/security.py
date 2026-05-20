from fastapi import Header, HTTPException, Query
import os
from .config import API_KEY

def verify_api_key(
    authorization: str | None = Header(default=None),
    api_key: str | None = Query(default=None),
    api_key_alt: str | None = Query(default=None, alias="api-key")
):
    if authorization == f"Bearer {API_KEY}":
        return
    if api_key == API_KEY:
        return
    if api_key_alt == API_KEY:
        return

    raise HTTPException(status_code=401, detail="Unauthorized")