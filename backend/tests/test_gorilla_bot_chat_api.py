"""Tests for Gorilla Bot chat API."""

import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy import select

from app.models.user import User
from app.models.gorilla_bot_conversation import GorillaBotConversation
from app.models.gorilla_bot_message import GorillaBotMessage
from app.services.auth_service import create_access_token, get_password_hash


@pytest.mark.asyncio
async def test_gorilla_bot_chat_creates_conversation(client, db):
    user = User(
        id=uuid.uuid4(),
        email=f"gorilla-bot-{uuid.uuid4()}@example.com",
        account_number=uuid.uuid4().hex[:20],
        password_hash=get_password_hash("testpass123"),
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()

    token = create_access_token({"sub": str(user.id), "email": user.email})
    response = await client.post(
        "/api/gorilla-bot/chat",
        json={"message": "How do free parlay limits work?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["conversation_id"]
    assert "remaining" in data["reply"].lower()
    assert "paywall" in data["reply"].lower() or "limits" in data["reply"].lower()

    conversations = await db.execute(select(GorillaBotConversation))
    messages = await db.execute(select(GorillaBotMessage))
    assert len(conversations.scalars().all()) == 1
    assert len(messages.scalars().all()) == 2
