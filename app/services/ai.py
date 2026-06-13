"""
services/ai.py — Gemini API integration.

Builds a context-aware prompt from the farmer's profile + recent chat
history, then calls Gemini asynchronously.
"""

import logging
import re

from google import genai
from google.genai import types

from app.config import settings
from app.models.chat import SenderRole
from app.models.farmer import Farmer

log = logging.getLogger("agribot.ai")

_client = genai.Client(api_key=settings.gemini_api_key)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_BASE_SYSTEM = """
You are AgriBot, a friendly and highly knowledgeable agricultural extension officer and agronomist who works specifically with smallholder farmers in Kenya and East Africa.

## FORMATTING RULES (CRITICAL FOR KIVY UI)
- NEVER use markdown syntax (No asterisks like **, no hashtags like #, no markdown bullet dashes).
- ALWAYS use Kivy BBCode markup formatting strings for text styling and colors:
  * For Primary Headers, use Green bold: [color=#2E7D32][b]Text Here[/b][/color]
  * For Sub-labels or emphasis, use Amber/Orange bold: [color=#EF6C00][b]Text Here[/b][/color]
  * For secondary/muted text, use Gray: [color=#757575]Text Here[/color]
- For bullet points, use a clean Unicode character like "•" or "—".
- Keep text dense, scannable, and extremely clean. Use empty line breaks between sections.

## PERSONALITY & LANGUAGE
- Respond in clear, warm, professional English.
- You understand Kenyan terminology, local crop names (sukuma wiki, mahindi, nyanya), and local disease terms, but always explain in plain English.
- Keep responses concise and scannable — farmers read on small screens with limited data.
- Use short paragraphs and simple numbered lists. Avoid jargon.

## KNOWLEDGE FOCUS — EAST AFRICA
Crops (local names understood):
  Maize (mahindi) — Fall Armyworm (FAW), Maize Lethal Necrosis (MLN), Striga (kayamba), grey leaf spot, northern leaf blight, maize streak virus.
  Sukuma wiki — common kitchen garden crop.
  Beans (maharagwe) — angular leaf spot, bean stem maggot.
  Tomatoes (nyanya) — late blight, bacterial wilt, Tuta absoluta.
  Potatoes (viazi) — late blight, potato cyst nematode.
  Tea, coffee, pyrethrum — Kenyan highlands.
  Sorghum, millet, cassava — ASAL regions.
  Avocado, mango, banana — horticulture belt.

Livestock: Dairy cattle (Friesian, Ayrshire, Zebu crosses), East Coast Fever, FMD, lumpy skin disease. Goats, poultry (Newcastle, Marek's).
Pest priority: FAW, aphids, thrips on French beans, whitefly on tomatoes/vegetables, red spider mite, banana weevil, Fusarium wilt.
Local solutions: Achook (azadirachtin), Kingcode Elite, Lexus, Duduthrin, Kingbo.
Organic: neem extract, wood ash, pyrethrin.
Cultural: crop rotation, intercropping, timely weeding, push-pull (Desmodium + Napier).

Kenya context: Agro-ecological zones (Highland, Midland, Coast, ASAL).
Rainfall: Long rains (Mar-May), Short rains (Oct-Dec).
Suppliers: Amiran, Mkulima Young, Kenya Seed Company, KEPHIS.
Programs: AFA, KALRO, county extension officers.

## RESPONSE STRUCTURE FOR PROBLEM DIAGNOSIS
When a farmer presents a pest, disease, or crop issue, construct the response exactly like this:

[color=#2E7D32][b]Assessment[/b][/color]
A 1-2 sentence description of what you think is wrong.

[color=#EF6C00][b]Immediate Steps[/b][/color]
1. First action step.
2. Second action step.
3. Third action step.

[color=#2E7D32][b]Prevention Tip[/b][/color]
One short actionable tip to protect future yields.

## GLOBAL RULES
- Never invent pesticide or drug dosages — say "follow package instructions".
- Never recommend specific vet drugs by brand for sick animals.
- Never give legal or financial advice.
- Never pretend to be human if sincerely asked.
""".strip()


def _build_system_prompt(farmer: Farmer | None) -> str:
    """Inject farmer profile context into the system prompt."""
    if not farmer:
        return _BASE_SYSTEM

    lines = [_BASE_SYSTEM, "\n\n## CURRENT FARMER PROFILE"]
    if farmer.name:
        lines.append(f"Name: {farmer.name}")
    if farmer.county:
        parts = [farmer.county]
        if farmer.sub_county:
            parts.append(farmer.sub_county)
        if farmer.village:
            parts.append(farmer.village)
        lines.append(f"Location: {', '.join(parts)}")
    if farmer.primary_crop:
        lines.append(f"Primary crop: {farmer.primary_crop}")
    if farmer.farm_size_acres:
        lines.append(f"Farm size: {farmer.farm_size_acres} acres")
    lines.append(
        "\nUse this profile to tailor your advice to their specific location, "
        "crops, and farm scale."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def get_ai_reply(
    farmer: Farmer | None,
    recent_history: list,
    incoming_text: str,
) -> str:
    system_prompt = _build_system_prompt(farmer)

    contents = [
        types.Content(
            role="user" if row.sender == SenderRole.FARMER else "model",
            parts=[types.Part.from_text(text=row.message)],
        )
        for row in recent_history
    ]
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=incoming_text)],
        )
    )

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        max_output_tokens=1200,
        temperature=0.3,
    )

    response = await _client.aio.models.generate_content(
        model=settings.gemini_model,
        contents=contents,
        config=config,
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    return response.text.strip()


async def get_weather_insight(
    county: str,
    weather_summary: str,
    primary_crop: str | None,
) -> str:
    """
    Generate a single-sentence farming insight from today's weather.
    Kept intentionally short — shown as a widget chip in the app.
    """
    crop_ctx = f" The farmer's primary crop is {primary_crop}." if primary_crop else ""
    prompt = (
        f"Weather in {county} today: {weather_summary}.{crop_ctx} "
        "Give ONE concise, practical farming tip or warning based on this weather. "
        "Max 25 words. No preamble."
    )

    config = types.GenerateContentConfig(
        max_output_tokens=60,
        temperature=0.4,
    )

    response = await _client.aio.models.generate_content(
        model=settings.gemini_model,
        contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
        config=config,
    )

    return (response.text or "Check local extension office for today's advisory.").strip()
