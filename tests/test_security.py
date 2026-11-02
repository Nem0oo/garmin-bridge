import os
import subprocess
import sys
from pathlib import Path

import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from common import security

from .conftest import API_KEY

SRC = Path(__file__).resolve().parent.parent / "src"


@pytest.fixture
def client():
    async def ok(_):
        return PlainTextResponse("ok")

    app = Starlette(routes=[Route("/mcp", ok, methods=["GET", "POST"])])
    app.add_middleware(security.ApiKeyMiddleware)
    return TestClient(app)


# --- Middleware -------------------------------------------------------------------


@pytest.mark.parametrize("auth", [f"Bearer {API_KEY}", f"bearer   {API_KEY} ", f"BEARER {API_KEY}"])
def test_good_key_in_header_passes(client, auth):
    r = client.get("/mcp", headers={"Authorization": auth})
    assert r.status_code == 200
    assert r.text == "ok"


@pytest.mark.parametrize("param", ["api_key", "api-key"])
def test_key_in_url_is_rejected(client, param):
    r = client.get(f"/mcp?{param}={API_KEY}")
    assert r.status_code == 401


@pytest.mark.parametrize(
    "auth",
    ["Bearer wrong", f"Bearer {API_KEY[:-1]}", f"Bearer {API_KEY}x", API_KEY, f"Basic {API_KEY}"],
)
def test_wrong_key_is_rejected(client, auth):
    assert client.get("/mcp", headers={"Authorization": auth}).status_code == 401


def test_missing_header_is_rejected_with_www_authenticate(client):
    r = client.get("/mcp")
    assert r.status_code == 401
    assert r.json() == {"error": "Unauthorized"}
    assert r.headers["www-authenticate"] == "Bearer"
    assert API_KEY not in r.text


def test_no_open_path(client):
    assert client.get("/health").status_code == 401


def test_non_utf8_header_does_not_crash():
    scope = {"type": "http", "path": "/mcp", "headers": [(b"authorization", b"Bearer \xe9\xff")]}
    assert not security._valid(scope)


@pytest.mark.anyio
async def test_websocket_is_refused():
    called, sent = [], []

    async def inner(scope, receive, send):
        called.append(scope)

    async def send(message):
        sent.append(message)

    await security.ApiKeyMiddleware(inner)({"type": "websocket", "path": "/mcp", "headers": []}, None, send)
    assert not called
    assert sent == [{"type": "websocket.close", "code": 1008}]


@pytest.mark.anyio
async def test_lifespan_passes_through():
    called = []

    async def inner(scope, receive, send):
        called.append(scope["type"])

    await security.ApiKeyMiddleware(inner)({"type": "lifespan"}, None, None)
    assert called == ["lifespan"]


# --- MCP app wiring ---------------------------------------------------------------


def test_mcp_app_requires_bearer():
    from mcp_server.main import app

    with TestClient(app) as c:
        assert c.get(f"/mcp?api_key={API_KEY}").status_code == 401
        assert c.get("/mcp", headers={"Authorization": f"Bearer {API_KEY}"}).status_code != 401


# --- Config -----------------------------------------------------------------------


def _import_config(key):
    env = {**os.environ, "GARMIN_API_KEY": key, "PYTHONPATH": str(SRC)}
    return subprocess.run([sys.executable, "-c", "import common.config"], env=env, capture_output=True, text=True)


def test_short_key_fails_at_startup():
    r = _import_config("k" * 31)
    assert r.returncode != 0
    assert "GARMIN_API_KEY must be at least 32 characters" in r.stderr


def test_32_char_key_is_accepted():
    assert _import_config("k" * 32).returncode == 0
