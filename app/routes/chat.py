"""
routes/chat.py — Chat endpoints.

POST /chat          — send a message, get AI reply
GET  /chat/{device_id} — paginated history
DELETE /chat/{device_id} — clear history
"""

import logging

from fastapi import APIRouter, HTTPException, Query, status

from app.models.chat import SenderRole
from app.schemas import ChatHistoryOut, ChatMessageOut, ChatRequest, ChatResponse
from app.services import ai as ai_svc
from app.services import chat as chat_svc
from app.services import farmer as farmer_svc

log = logging.getLogger("agribot.routes.chat")

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def send_message(body: ChatRequest):
    farmer = await farmer_svc.get_farmer_by_device_id(body.device_id)
    if not farmer:
        # Auto-create a minimal profile so the farmer can still chat
        farmer = await farmer_svc.get_or_create_farmer(body.device_id)

    # Log farmer message
    await chat_svc.log_message(farmer.id, SenderRole.FARMER, body.message)

    # Fetch recent context for Gemini
    recent = await chat_svc.fetch_recent_context(farmer.id, limit=10)

    # Call Gemini
    try:
        reply = await ai_svc.get_ai_reply(
            farmer=farmer,
            recent_history=recent,
            incoming_text=body.message,
        )
    except Exception as exc:
        log.error("Gemini error for device_id=%s: %s", body.device_id, exc)
        reply = (
            "Sorry, I'm having a brief technical issue. "
            "Please try again in a moment. 🌱"
        )

    # Log AI reply
    await chat_svc.log_message(farmer.id, SenderRole.AI, reply)

    # Return the updated tail of history
    updated = await chat_svc.fetch_recent_context(farmer.id, limit=20)
    return ChatResponse(
        reply=reply,
        messages=[ChatMessageOut.model_validate(m) for m in updated],
    )


@router.get("/{device_id}", response_model=ChatHistoryOut)
async def get_history(
    device_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    farmer = await farmer_svc.get_farmer_by_device_id(device_id)
    if not farmer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer not found")

    messages, total = await chat_svc.fetch_history(farmer.id, offset=offset, limit=limit)
    return ChatHistoryOut(
        messages=[ChatMessageOut.model_validate(m) for m in messages],
        total=total,
    )


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def clear_history(device_id: str):
    """Let the farmer clear their local + server chat history."""
    from sqlalchemy import delete as sql_delete
    from app.database import get_db
    from app.models.chat import ChatHistory

    farmer = await farmer_svc.get_farmer_by_device_id(device_id)
    if not farmer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer not found")

    async with get_db() as db:
        await db.execute(
            sql_delete(ChatHistory).where(ChatHistory.farmer_id == farmer.id)
        )
        await db.commit()
