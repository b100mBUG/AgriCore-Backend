"""
config.py — Environment-driven settings via pydantic-settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # Weather (Open-Meteo is free, no key needed; this is for future paid provider)
    weather_api_key: str = ""

    # Admin
    admin_api_key: str = "change-me-in-production"

    # DB
    database_url: str = "sqlite+aiosqlite:///./agribot.db"

    # Behaviour
    context_window_messages: int = 10  # messages fed into Gemini context

    # CORS — comma-separated origins for the mobile app / web admin
    allowed_origins: str = "*"


settings = Settings()
