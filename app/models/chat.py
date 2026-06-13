"""
models/chat.py — Append-only message log per farmer.
"""

from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class SenderRole(str, PyEnum):
    FARMER = "farmer"
    AI = "ai"


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    farmer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("farmers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender: Mapped[SenderRole] = mapped_column(Enum(SenderRole), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    farmer: Mapped["Farmer"] = relationship("Farmer", back_populates="chat_history")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<ChatHistory id={self.id} farmer_id={self.farmer_id} "
            f"sender={self.sender} ts={self.timestamp}>"
        )
