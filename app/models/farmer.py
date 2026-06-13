"""
models/farmer.py — Farmer profile (replaces UserSession's phone-only identity).

A Farmer now has a proper profile with location details they supply during
onboarding. Location is used for weather lookups without relying on GPS.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Farmer(Base):
    __tablename__ = "farmers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Identity — device-generated UUID stored locally; no phone required
    device_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    # Profile
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # Location — farmer-supplied during onboarding or settings edit
    county: Mapped[str | None] = mapped_column(String(80), nullable=True)
    sub_county: Mapped[str | None] = mapped_column(String(80), nullable=True)
    village: Mapped[str | None] = mapped_column(String(80), nullable=True)
    # Lat/lon resolved from the text location (geocoded once on the backend)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Farm context — helps Gemini give relevant advice
    primary_crop: Mapped[str | None] = mapped_column(String(120), nullable=True)
    farm_size_acres: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    chat_history: Mapped[list["ChatHistory"]] = relationship(  # noqa: F821
        "ChatHistory",
        back_populates="farmer",
        cascade="all, delete-orphan",
        order_by="ChatHistory.timestamp",
    )

    def __repr__(self) -> str:
        return f"<Farmer id={self.id} device_id={self.device_id!r} county={self.county!r}>"
