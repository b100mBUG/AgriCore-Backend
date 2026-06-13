"""
routes/farmers.py — Farmer onboarding and profile management.

POST /farmers/register   — first-time registration (device_id + optional profile)
GET  /farmers/{device_id} — fetch profile
PATCH /farmers/{device_id} — update profile (name, location, crops, etc.)
"""

import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas import FarmerCreate, FarmerOut, FarmerUpdate
from app.services import farmer as farmer_svc

log = logging.getLogger("agribot.routes.farmers")

router = APIRouter(prefix="/farmers", tags=["Farmers"])


@router.post("/register", response_model=FarmerOut, status_code=status.HTTP_201_CREATED)
async def register_farmer(body: FarmerCreate):
    """
    Called once on first app launch. The app generates a UUID locally and
    sends it as device_id. Subsequent requests use the same device_id.
    """
    existing = await farmer_svc.get_farmer_by_device_id(body.device_id)
    if existing:
        # Idempotent — return the existing profile
        return existing
    return await farmer_svc.create_farmer(body)


@router.get("/{device_id}", response_model=FarmerOut)
async def get_farmer(device_id: str):
    farmer = await farmer_svc.get_farmer_by_device_id(device_id)
    if not farmer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer not found")
    return farmer


@router.patch("/{device_id}", response_model=FarmerOut)
async def update_farmer(device_id: str, body: FarmerUpdate):
    farmer = await farmer_svc.update_farmer(device_id, body)
    if not farmer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer not found")
    return farmer
