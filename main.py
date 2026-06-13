"""
main.py — App factory. Lifespan + router registration only.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes.farmers import router as farmers_router
from app.routes.chat import router as chat_router
from app.routes.weather import router as weather_router
from app.routes.officers import router as officers_router
from app.routes.admin import router as admin_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
log = logging.getLogger("agribot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("AgriBot starting — initialising database...")
    log.info("Database ready.")
    yield
    log.info("AgriBot shutting down.")


app = FastAPI(
    title="AgriBot — Kenya Farming Assistant API",
    version="3.0.0",
    description="Standalone mobile app backend. No WhatsApp dependency.",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.allowed_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(farmers_router)
app.include_router(chat_router)
app.include_router(weather_router)
app.include_router(officers_router)
app.include_router(admin_router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": "3.0.0"}
