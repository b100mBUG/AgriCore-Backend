"""
routes/admin.py — Admin analytics endpoint.
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.database import get_db
from app.models.chat import ChatHistory, SenderRole
from app.models.farmer import Farmer
from app.routes.deps import require_admin
from app.schemas import AnalyticsOut

log = logging.getLogger("agribot.routes.admin")

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin)],
)


@router.get("/analytics", response_model=AnalyticsOut)
async def get_analytics():
    async with get_db() as db:
        total_farmers = (
            await db.execute(select(func.count(Farmer.id)))
        ).scalar_one()

        total_messages = (
            await db.execute(select(func.count(ChatHistory.id)))
        ).scalar_one()

        sender_result = await db.execute(
            select(ChatHistory.sender, func.count(ChatHistory.id))
            .group_by(ChatHistory.sender)
        )
        messages_by_sender = {row[0].value: row[1] for row in sender_result.all()}

        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        active_last_7 = (
            await db.execute(
                select(func.count(ChatHistory.farmer_id.distinct())).where(
                    ChatHistory.timestamp >= week_ago
                )
            )
        ).scalar_one()

        county_result = await db.execute(
            select(Farmer.county, func.count(Farmer.id))
            .where(Farmer.county.isnot(None))
            .group_by(Farmer.county)
            .order_by(func.count(Farmer.id).desc())
            .limit(10)
        )
        top_counties = [
            {"county": row[0], "farmers": row[1]} for row in county_result.all()
        ]

    return AnalyticsOut(
        total_farmers=total_farmers,
        total_messages=total_messages,
        messages_by_sender=messages_by_sender,
        top_counties=top_counties,
        active_farmers_last_7_days=active_last_7,
    )
