"""
services/farmer.py — Farmer profile CRUD + geocoding on save.
"""

import logging

from sqlalchemy import select

from app.database import get_db
from app.models.farmer import Farmer
from app.schemas import FarmerCreate, FarmerUpdate
from app.services import weather as weather_svc

log = logging.getLogger("agribot.farmer")


async def get_farmer_by_device_id(device_id: str) -> Farmer | None:
    async with get_db() as db:
        result = await db.execute(
            select(Farmer).where(Farmer.device_id == device_id)
        )
        return result.scalar_one_or_none()


async def get_or_create_farmer(device_id: str) -> Farmer:
    async with get_db() as db:
        result = await db.execute(
            select(Farmer).where(Farmer.device_id == device_id)
        )
        farmer = result.scalar_one_or_none()
        if farmer is None:
            farmer = Farmer(device_id=device_id)
            db.add(farmer)
            await db.commit()
            await db.refresh(farmer)
            log.info("New farmer registered: device_id=%s", device_id)
        return farmer


async def create_farmer(data: FarmerCreate) -> Farmer:
    lat, lon = await _resolve_coords(data.county, data.sub_county, data.village)

    async with get_db() as db:
        farmer = Farmer(
            **data.model_dump(),
            latitude=lat,
            longitude=lon,
        )
        db.add(farmer)
        await db.commit()
        await db.refresh(farmer)
        log.info("Farmer created: device_id=%s county=%s", farmer.device_id, farmer.county)
        return farmer


async def update_farmer(device_id: str, data: FarmerUpdate) -> Farmer | None:
    async with get_db() as db:
        result = await db.execute(
            select(Farmer).where(Farmer.device_id == device_id)
        )
        farmer = result.scalar_one_or_none()
        if not farmer:
            return None

        updates = data.model_dump(exclude_none=True)
        for field, value in updates.items():
            setattr(farmer, field, value)

        # Re-geocode if location fields changed
        location_fields = {"county", "sub_county", "village"}
        if location_fields & set(updates.keys()):
            lat, lon = await _resolve_coords(farmer.county, farmer.sub_county, farmer.village)
            farmer.latitude = lat
            farmer.longitude = lon

        await db.commit()
        await db.refresh(farmer)
        return farmer


async def _resolve_coords(
    county: str | None,
    sub_county: str | None,
    village: str | None,
) -> tuple[float | None, float | None]:
    """Build the best query we can and geocode it."""
    parts = [p for p in [village, sub_county, county, "Kenya"] if p]
    if not parts or parts == ["Kenya"]:
        return None, None
    query = ", ".join(parts)
    coords = await weather_svc.geocode_location(query)
    if coords:
        return coords
    # Fallback: try county only
    if county:
        coords = await weather_svc.geocode_location(f"{county}, Kenya")
    return coords or (None, None)
