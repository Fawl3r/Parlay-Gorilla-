"""Tests for authentication flows"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from datetime import datetime, timedelta, timezone

from app.models.user import User
from app.services.auth_service import create_access_token, get_password_hash


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, db: AsyncSession):
    """Test user registration"""
    email = f"test-{uuid.uuid4()}@example.com"
    response = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "testpass123",
            "username": "testuser"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["email"] == email
    assert "account_number" in data["user"]
    assert isinstance(data["user"]["account_number"], str)
    assert len(data["user"]["account_number"]) >= 6


@pytest.mark.asyncio
async def test_login_is_case_insensitive_for_email(client: AsyncClient, db: AsyncSession):
    """Login should succeed even if the stored email casing differs."""
    stored_email = f"MiXeD-{uuid.uuid4()}@Example.com"
    password = "testpass123"

    user = User(
        id=uuid.uuid4(),
        email=stored_email,  # intentionally mixed-case (legacy rows)
        account_number=f"{uuid.uuid4().hex[:20]}",
        password_hash=get_password_hash(password),
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()

    response = await client.post(
        "/api/auth/login",
        json={"email": stored_email.lower(), "password": password},
    )
    assert response.status_code == 200, response.text


@pytest.mark.asyncio
async def test_register_and_login_with_long_password(client: AsyncClient):
    """Long passwords (>72 bytes) should work for both register and login."""
    email = f"longpw-{uuid.uuid4()}@example.com"
    long_password = "A" * 100  # 100 bytes (ASCII), exceeds bcrypt's 72-byte input limit

    register_response = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": long_password,
        },
    )
    assert register_response.status_code == 200, register_response.text

    login_response = await client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": long_password,
        },
    )
    assert login_response.status_code == 200, login_response.text


@pytest.mark.asyncio
async def test_login_user(client: AsyncClient, db: AsyncSession):
    """Test user login"""
    email = f"login-{uuid.uuid4()}@example.com"
    password = "testpass123"
    # First register
    await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
        }
    )
    
    # Then login
    response = await client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password,
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "user" in data


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Test login with invalid credentials"""
    response = await client.post(
        "/api/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "wrongpass",
        }
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, db: AsyncSession):
    """Test getting current user with valid token"""
    email = f"current-{uuid.uuid4()}@example.com"
    # Register and get token
    register_response = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "testpass123",
        }
    )
    token = register_response.json()["access_token"]
    account_number = register_response.json()["user"]["account_number"]
    
    # Get current user
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert data["account_number"] == account_number


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: AsyncClient):
    """Test getting current user with invalid token"""
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_sets_access_token_cookie(client: AsyncClient, db: AsyncSession):
    email = f"cookie-{uuid.uuid4()}@example.com"
    password = "testpass123"

    user = User(
        id=uuid.uuid4(),
        email=email,
        account_number=f"{uuid.uuid4().hex[:20]}",
        password_hash=get_password_hash(password),
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()

    r2 = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert r2.status_code == 200, r2.text
    assert "set-cookie" in {k.lower(): v for k, v in r2.headers.items()}


@pytest.mark.asyncio
async def test_me_accepts_cookie_auth_without_authorization_header(client: AsyncClient, db: AsyncSession):
    email = f"cookie-me-{uuid.uuid4()}@example.com"
    password = "testpass123"

    user = User(
        id=uuid.uuid4(),
        email=email,
        account_number=f"{uuid.uuid4().hex[:20]}",
        password_hash=get_password_hash(password),
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()

    # Login to establish cookie session.
    login = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text

    # httpx AsyncClient should persist cookies from the response automatically.
    me = await client.get("/api/auth/me")
    assert me.status_code == 200, me.text


@pytest.mark.asyncio
async def test_me_rejects_invalid_token_subject(client: AsyncClient):
    token = create_access_token(
        {"sub": "not-a-uuid", "email": "test@example.com"},
        expires_delta=timedelta(minutes=5),
    )
    r = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
    assert r.json().get("detail") == "Invalid token subject"

