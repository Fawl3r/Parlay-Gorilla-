"""
Main orchestration for Gorilla Bot chat.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional
import uuid
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.services.ai_text_sanitizer import AiTextSanitizer
from app.services.gorilla_bot.conversation_repository import GorillaBotConversationRepository
from app.services.gorilla_bot.message_repository import GorillaBotMessageRepository
from app.services.gorilla_bot.openai_client import GorillaBotOpenAIClient
from app.services.gorilla_bot.prompt_builder import GorillaBotPromptBuilder, GorillaBotContextSnippet
from app.services.gorilla_bot.user_context_builder import GorillaBotUserContextBuilder
from app.services.gorilla_bot.kb_retriever import GorillaBotKnowledgeRetriever

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GorillaBotCitation:
    title: str
    source_path: str
    source_url: Optional[str]


@dataclass(frozen=True)
class GorillaBotChatResult:
    conversation_id: str
    message_id: str
    reply: str
    citations: List[GorillaBotCitation]


class GorillaBotConversationTitleGenerator:
    def generate(self, question: str) -> str:
        words = [w for w in (question or "").strip().split() if w]
        if not words:
            return "Gorilla Bot Conversation"
        title = " ".join(words[:8])
        return title[:100]


class GorillaBotFallbackResponder:
    def build(self, citations: List[GorillaBotCitation]) -> str:
        if citations:
            titles = ", ".join(citation.title for citation in citations)
            return (
                "Gorilla Bot is temporarily unavailable. "
                f"Here are the most relevant resources to review: {titles}. "
                "Please try again in a moment if you need more detail."
            )
        return (
            "Gorilla Bot is temporarily unavailable. "
            "Please try again in a moment."
        )


class GorillaBotManager:
    """Coordinates Gorilla Bot chat requests."""

    def __init__(self, db: AsyncSession):
        self._db = db
        self._openai = GorillaBotOpenAIClient()
        self._prompt_builder = GorillaBotPromptBuilder()
        self._user_context_builder = GorillaBotUserContextBuilder(db)
        self._retriever = GorillaBotKnowledgeRetriever(self._openai)
        self._conversations = GorillaBotConversationRepository(db)
        self._messages = GorillaBotMessageRepository(db)
        self._sanitizer = AiTextSanitizer()
        self._title_generator = GorillaBotConversationTitleGenerator()
        self._fallback = GorillaBotFallbackResponder()

    async def chat(self, user: User, question: str, conversation_id: Optional[uuid.UUID]) -> GorillaBotChatResult:
        if not settings.gorilla_bot_enabled:
            raise RuntimeError("Gorilla Bot is disabled.")

        try:
            conversation = await self._get_or_create_conversation(user, conversation_id, question)
            await self._messages.add_message(conversation.id, "user", question)

            user_context = await self._user_context_builder.build(user)
            snippets = await self._retriever.retrieve(question)
            citations = self._build_citations(snippets)

            reply = await self._generate_reply(question, user_context, snippets, citations)
            assistant_message = await self._messages.add_message(
                conversation.id,
                "assistant",
                reply,
                citations=[citation.__dict__ for citation in citations] if citations else None,
            )

            await self._conversations.mark_last_message(conversation.id, datetime.now(timezone.utc))
            await self._db.commit()

            return GorillaBotChatResult(
                conversation_id=str(conversation.id),
                message_id=str(assistant_message.id),
                reply=reply,
                citations=citations,
            )
        except Exception:
            await self._db.rollback()
            raise

    async def _get_or_create_conversation(
        self,
        user: User,
        conversation_id: Optional[uuid.UUID],
        question: str,
    ):
        if conversation_id:
            conversation = await self._conversations.get_by_id(conversation_id, user.id)
            if conversation:
                return conversation
            raise ValueError("Conversation not found.")

        title = self._title_generator.generate(question)
        return await self._conversations.create(user.id, title=title)

    async def _generate_reply(
        self,
        question: str,
        user_context,
        snippets: List[GorillaBotContextSnippet],
        citations: List[GorillaBotCitation],
    ) -> str:
        if not self._openai.enabled:
            return self._fallback.build(citations)

        messages = self._prompt_builder.build_messages(question, user_context, snippets)
        try:
            response = await self._openai.chat_completion(
                messages=messages,
                max_tokens=int(settings.gorilla_bot_max_response_tokens),
            )
        except Exception as exc:
            logger.warning("Gorilla Bot OpenAI chat failed: %s", exc)
            response = self._fallback.build(citations)

        return self._sanitizer.sanitize(response)

    def _build_citations(self, snippets: List[GorillaBotContextSnippet]) -> List[GorillaBotCitation]:
        citations: List[GorillaBotCitation] = []
        seen = set()
        for snippet in snippets:
            key = (snippet.title, snippet.source_path)
            if key in seen:
                continue
            seen.add(key)
            citations.append(
                GorillaBotCitation(
                    title=snippet.title,
                    source_path=snippet.source_path,
                    source_url=snippet.source_url,
                )
            )
            if len(citations) >= 3:
                break
        return citations
