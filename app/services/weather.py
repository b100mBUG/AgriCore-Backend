import logging
from datetime import date
import httpx

log = logging.getLogger("agribot.weather")

# WeatherAPI handles both forecasting and string query geocoding at this single endpoint
_WEATHER_URL = "https://api.weatherapi.com/v1/forecast.json"

# WeatherAPI key pulled from your environment configuration
# Make sure to add WEATHER_API_KEY to your .env or settings config
from app.config import settings 
WEATHER_API_KEY = settings.weather_api_key


async def geocode_location(query: str) -> tuple[float, float] | None:
    """
    Keep this function signature intact so your registration routes don't break.
    WeatherAPI natively accepts strings, but if your database needs explicit lat/lon,
    we can fetch a lightweight payload here to extract them.
    """
    params = {"key": WEATHER_API_KEY, "q": query, "days": 1}
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(_WEATHER_URL, params=params)
            if resp.status_code != 200:
                return None
            data = resp.json()
            loc = data.get("location", {})
            return loc.get("lat"), loc.get("lon")
    except Exception as exc:
        log.warning("Geocoding failed for %r: %s", query, exc)
        return None


async def fetch_weather(lat: float, lon: float) -> dict:
    """
    Fetch current conditions and 7-day daily forecast from WeatherAPI.
    Accepts lat/lon floats matching your existing architecture.
    """
    params = {
        "key": WEATHER_API_KEY,
        "q": f"{lat},{lon}",
        "days": 7,
        "aqi": "no",
        "alerts": "no"
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(_WEATHER_URL, params=params)
        resp.raise_for_status()
        return resp.json()


def parse_weather(raw: dict) -> dict:
    """Convert WeatherAPI JSON structure to the exact dict structure your schema expects."""
    c = raw["current"]
    f_days = raw["forecast"]["forecastday"]

    # Map WeatherAPI layout cleanly to your existing output schema
    current = {
        "temperature_c": round(c["temp_c"], 1),
        "feels_like_c": round(c["feelslike_c"], 1),
        "humidity_pct": int(c["humidity"]),
        "wind_kph": round(c["wind_kph"], 1),
        "condition": c["condition"]["text"],  # WeatherAPI gives human-readable text natively!
        "is_day": bool(c["is_day"]),
    }

    forecast = []
    for day_data in f_days:
        day_metrics = day_data["day"]
        forecast.append({
            "date": day_data["date"],
            "max_temp_c": round(day_metrics["maxtemp_c"], 1),
            "min_temp_c": round(day_metrics["mintemp_c"], 1),
            "precipitation_mm": round(day_metrics["totalprecip_mm"] or 0, 1),
            "condition": day_metrics["condition"]["text"],  # No WMO mapping dictionary needed
            "uv_index": round(day_metrics["uv"] or 0, 1),
        })

    return {"current": current, "forecast": forecast}