"""Unit tests for the health endpoint and app configuration."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.backend.main import app


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_health_returns_200() -> None:
    """GET /api/health returns HTTP 200."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_health_response_body() -> None:
    """GET /api/health returns {"status": "healthy"}."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
    assert response.json() == {"status": "healthy"}


@pytest.mark.anyio
async def test_cors_headers_present() -> None:
    """Response includes CORS allow-origin for localhost:5173."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.options(
            "/api/health",
            headers={
                "origin": "http://localhost:5173",
                "access-control-request-method": "GET",
            },
        )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
