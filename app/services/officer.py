"""
services/officer.py — ExtensionOfficer CRUD.
"""

import logging

from sqlalchemy import select

from app.database import get_db
from app.models.officer import ExtensionOfficer, OfficerSpecialization
from app.schemas import OfficerCreate, OfficerUpdate

log = logging.getLogger("agribot.officer")


async def create_officer(data: OfficerCreate) -> ExtensionOfficer:
    async with get_db() as db:
        officer = ExtensionOfficer(**data.model_dump())
        db.add(officer)
        await db.commit()
        await db.refresh(officer)
        log.info("Officer created: %s (%s)", officer.name, officer.phone_number)
        return officer


async def list_officers(active_only: bool = True) -> list[ExtensionOfficer]:
    async with get_db() as db:
        query = select(ExtensionOfficer)
        if active_only:
            query = query.where(ExtensionOfficer.is_active.is_(True))
        result = await db.execute(query.order_by(ExtensionOfficer.name))
        return list(result.scalars().all())


async def get_officer(officer_id: int) -> ExtensionOfficer | None:
    async with get_db() as db:
        result = await db.execute(
            select(ExtensionOfficer).where(ExtensionOfficer.id == officer_id)
        )
        return result.scalar_one_or_none()


async def update_officer(officer_id: int, data: OfficerUpdate) -> ExtensionOfficer | None:
    async with get_db() as db:
        result = await db.execute(
            select(ExtensionOfficer).where(ExtensionOfficer.id == officer_id)
        )
        officer = result.scalar_one_or_none()
        if not officer:
            return None
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(officer, field, value)
        await db.commit()
        await db.refresh(officer)
        return officer


async def delete_officer(officer_id: int) -> bool:
    async with get_db() as db:
        result = await db.execute(
            select(ExtensionOfficer).where(ExtensionOfficer.id == officer_id)
        )
        officer = result.scalar_one_or_none()
        if not officer:
            return False
        await db.delete(officer)
        await db.commit()
        return True


async def pick_best_officer(
    specialization: OfficerSpecialization | None = None,
) -> ExtensionOfficer | None:
    async with get_db() as db:
        if specialization and specialization != OfficerSpecialization.GENERAL:
            result = await db.execute(
                select(ExtensionOfficer)
                .where(
                    ExtensionOfficer.is_active.is_(True),
                    ExtensionOfficer.specialization == specialization,
                )
                .limit(1)
            )
            officer = result.scalar_one_or_none()
            if officer:
                return officer
        result = await db.execute(
            select(ExtensionOfficer)
            .where(ExtensionOfficer.is_active.is_(True))
            .order_by(ExtensionOfficer.id)
            .limit(1)
        )
        return result.scalar_one_or_none()
