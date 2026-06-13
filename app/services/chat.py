"""
services/chat.py — Chat history DB operations.
"""

import logging

from sqlalchemy import desc, select

from app.database import get_db
from app.models.chat import ChatHistory, SenderRole

log = logging.getLogger("agribot.chat")


async def log_message(farmer_id: int, sender: SenderRole, message: str) -> ChatHistory:
    async with get_db() as db:
        entry = ChatHistory(
            farmer_id=farmer_id,
            sender=sender,
            message=message,
        )
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        return entry


async def fetch_recent_context(farmer_id: int, limit: int) -> list[ChatHistory]:
    """Return the N most recent messages in chronological order (oldest first)."""
    async with get_db() as db:
        result = await db.execute(
            select(ChatHistory)
            .where(ChatHistory.farmer_id == farmer_id)
            .order_by(desc(ChatHistory.timestamp))
            .limit(limit)
        )
        rows = result.scalars().all()
        return list(reversed(rows))


async def fetch_history(farmer_id: int, offset: int = 0, limit: int = 50) -> tuple[list[ChatHistory], int]:
    """Paginated history with total count."""
    async with get_db() as db:
        count_result = await db.execute(
            select(ChatHistory).where(ChatHistory.farmer_id == farmer_id)
        )
        total = len(count_result.scalars().all())

        result = await db.execute(
            select(ChatHistory)
            .where(ChatHistory.farmer_id == farmer_id)
            .order_by(ChatHistory.timestamp)
            .offset(offset)
            .limit(limit)
        )
        messages = result.scalars().all()
        return list(messages), total
