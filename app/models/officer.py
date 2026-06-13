"""
models/officer.py — Extension officer directory.
"""

from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class OfficerSpecialization(str, PyEnum):
    CROPS = "crops"
    LIVESTOCK = "livestock"
    HORTICULTURE = "horticulture"
    AGROFORESTRY = "agroforestry"
    GENERAL = "general"


class ExtensionOfficer(Base):
    __tablename__ = "extension_officers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    county: Mapped[str | None] = mapped_column(String(80), nullable=True)
    specialization: Mapped[OfficerSpecialization] = mapped_column(
        Enum(OfficerSpecialization),
        nullable=False,
        default=OfficerSpecialization.GENERAL,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<ExtensionOfficer id={self.id} name={self.name!r} county={self.county!r}>"
