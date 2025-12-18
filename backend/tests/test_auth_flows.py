"""Tests for authentication flows"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.models.user import User


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

