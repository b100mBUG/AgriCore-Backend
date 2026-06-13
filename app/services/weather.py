"""
services/weather.py — Weather data via Open-Meteo (free, no API key required).

We geocode the farmer's county/village using the Open-Meteo geocoding API,
then fetch current conditions + 7-day forecast.

Design: intentionally simple — no overengineering.
"""

import logging
from datetime import date

import httpx

log = logging.getLogger("agribot.weather")

_GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather interpretation codes → human-readable
_WMO_CODES: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


def _wmo_label(code: int) -> str:
    return _WMO_CODES.get(code, f"Code {code}")


async def geocode_location(query: str) -> tuple[float, float] | None:
    """
    Resolve a text location (e.g. 'Nakuru, Kenya') to (lat, lon).
    Returns None if nothing found.
    """
    params = {"name": query, "count": 1, "language": "en", "format": "json"}
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(_GEO_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results")
            if not results:
                return None
            r = results[0]
            return r["latitude"], r["longitude"]
    except Exception as exc:
        log.warning("Geocoding failed for %r: %s", query, exc)
        return None


async def fetch_weather(lat: float, lon: float) -> dict:
    """
    Fetch current conditions and 7-day daily forecast from Open-Meteo.
    Returns a raw dict; callers build the schema object.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m",
            "apparent_temperature",
            "relative_humidity_2m",
            "wind_speed_10m",
            "weather_code",
            "is_day",
        ],
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "weather_code",
            "uv_index_max",
        ],
        "timezone": "Africa/Nairobi",
        "forecast_days": 7,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(_WEATHER_URL, params=params)
        resp.raise_for_status()
        return resp.json()


def parse_weather(raw: dict) -> dict:
    """Convert Open-Meteo JSON to the dict structure our schema expects."""
    c = raw["current"]
    d = raw["daily"]

    current = {
        "temperature_c": round(c["temperature_2m"], 1),
        "feels_like_c": round(c["apparent_temperature"], 1),
        "humidity_pct": int(c["relative_humidity_2m"]),
        "wind_kph": round(c["wind_speed_10m"], 1),
        "condition": _wmo_label(c["weather_code"]),
        "is_day": bool(c["is_day"]),
    }

    forecast = []
    for i, day_date in enumerate(d["time"]):
        forecast.append({
            "date": day_date,
            "max_temp_c": round(d["temperature_2m_max"][i], 1),
            "min_temp_c": round(d["temperature_2m_min"][i], 1),
            "precipitation_mm": round(d["precipitation_sum"][i] or 0, 1),
            "condition": _wmo_label(d["weather_code"][i]),
            "uv_index": round(d["uv_index_max"][i] or 0, 1),
        })

    return {"current": current, "forecast": forecast}
