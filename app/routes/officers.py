"""
routes/officers.py — Extension officer endpoints.

GET  /officers          — public, no auth (farmer-facing directory)
POST /officers          — admin only
PATCH/DELETE /officers  — admin only
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas import OfficerCreate, OfficerOut, OfficerUpdate
from app.services import officer as officer_svc
from app.routes.deps import require_admin

log = logging.getLogger("agribot.routes.officers")

router = APIRouter(prefix="/officers", tags=["Officers"])


# ── Public ────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[OfficerOut])
async def list_officers(active_only: bool = True):
    """Farmer-facing officer directory. No auth required."""
    return await officer_svc.list_officers(active_only=active_only)


@router.get("/{officer_id}", response_model=OfficerOut)
async def get_officer(officer_id: int):
    officer = await officer_svc.get_officer(officer_id)
    if not officer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Officer not found")
    return officer


# ── Admin only ────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=OfficerOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_officer(body: OfficerCreate):
    return await officer_svc.create_officer(body)


@router.patch(
    "/{officer_id}",
    response_model=OfficerOut,
    dependencies=[Depends(require_admin)],
)
async def update_officer(officer_id: int, body: OfficerUpdate):
    officer = await officer_svc.update_officer(officer_id, body)
    if not officer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Officer not found")
    return officer


@router.delete(
    "/{officer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
async def delete_officer(officer_id: int):
    deleted = await officer_svc.delete_officer(officer_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Officer not found")
