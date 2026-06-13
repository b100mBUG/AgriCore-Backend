"""
schemas.py — All Pydantic request/response models.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.officer import OfficerSpecialization
from app.models.chat import SenderRole


# ---------------------------------------------------------------------------
# Farmer
# ---------------------------------------------------------------------------

class FarmerCreate(BaseModel):
    device_id: str = Field(..., min_length=8, max_length=64)
    name: Optional[str] = Field(None, max_length=120)
    county: Optional[str] = Field(None, max_length=80)
    sub_county: Optional[str] = Field(None, max_length=80)
    village: Optional[str] = Field(None, max_length=80)
    primary_crop: Optional[str] = Field(None, max_length=120)
    farm_size_acres: Optional[float] = None


class FarmerUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=120)
    county: Optional[str] = Field(None, max_length=80)
    sub_county: Optional[str] = Field(None, max_length=80)
    village: Optional[str] = Field(None, max_length=80)
    primary_crop: Optional[str] = Field(None, max_length=120)
    farm_size_acres: Optional[float] = None


class FarmerOut(BaseModel):
    id: int
    device_id: str
    name: Optional[str]
    county: Optional[str]
    sub_county: Optional[str]
    village: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    primary_crop: Optional[str]
    farm_size_acres: Optional[float]
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    device_id: str
    message: str = Field(..., min_length=1, max_length=4000)


class ChatMessageOut(BaseModel):
    id: int
    sender: SenderRole
    message: str
    timestamp: datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    reply: str
    messages: list[ChatMessageOut]


class ChatHistoryOut(BaseModel):
    messages: list[ChatMessageOut]
    total: int


# ---------------------------------------------------------------------------
# Weather
# ---------------------------------------------------------------------------

class WeatherCurrent(BaseModel):
    temperature_c: float
    feels_like_c: float
    humidity_pct: int
    wind_kph: float
    condition: str          # e.g. "Partly cloudy"
    is_day: bool


class WeatherForecastDay(BaseModel):
    date: str               # YYYY-MM-DD
    max_temp_c: float
    min_temp_c: float
    precipitation_mm: float
    condition: str
    uv_index: float


class WeatherOut(BaseModel):
    location: str           # county / village label
    latitude: float
    longitude: float
    current: WeatherCurrent
    forecast: list[WeatherForecastDay]  # 7 days
    farming_insight: str    # Gemini-generated one-liner


# ---------------------------------------------------------------------------
# Extension Officers
# ---------------------------------------------------------------------------

class OfficerCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    phone_number: str = Field(..., min_length=7, max_length=20)
    county: Optional[str] = Field(None, max_length=80)
    specialization: OfficerSpecialization = OfficerSpecialization.GENERAL
    notes: Optional[str] = None


class OfficerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    phone_number: Optional[str] = Field(None, min_length=7, max_length=20)
    county: Optional[str] = Field(None, max_length=80)
    specialization: Optional[OfficerSpecialization] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class OfficerOut(BaseModel):
    id: int
    name: str
    phone_number: str
    county: Optional[str]
    specialization: OfficerSpecialization
    notes: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Admin Analytics
# ---------------------------------------------------------------------------

class AnalyticsOut(BaseModel):
    total_farmers: int
    total_messages: int
    messages_by_sender: dict[str, int]
    top_counties: list[dict]
    active_farmers_last_7_days: int
