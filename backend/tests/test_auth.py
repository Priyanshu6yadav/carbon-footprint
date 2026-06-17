"""
CarbonTrack — Auth endpoint tests.
"""
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


import uuid

@pytest.mark.asyncio
async def test_register_success():
    uid = uuid.uuid4().hex[:8]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/auth/register", json={
            "email": f"test_{uid}@example.com",
            "username": f"user_{uid}",
            "password": "SecurePass123",
            "full_name": "Test User",
        })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == f"test_{uid}@example.com"
    assert data["user"]["username"] == f"user_{uid}"


@pytest.mark.asyncio
async def test_register_weak_password():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/auth/register", json={
            "email": "test2@example.com",
            "username": "testuser2",
            "password": "weak",
        })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_username():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/auth/register", json={
            "email": "test3@example.com",
            "username": "invalid user name!",  # spaces and special chars not allowed
            "password": "SecurePass123",
        })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_wrong_password():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "WrongPass123",
        })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/auth/me")
    assert response.status_code == 401  # No bearer token


@pytest.mark.asyncio
async def test_register_too_long_password():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/auth/register", json={
            "email": "longpwd@example.com",
            "username": "longpwduser",
            "password": "SecurePass123" * 10,  # 130 characters, > 72 limit
        })
    assert response.status_code == 422
