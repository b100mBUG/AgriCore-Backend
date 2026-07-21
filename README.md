# AgriBot: Kenya Farming Assistant API

Backend for AgriBot, an AI farming assistant for smallholder farmers in Kenya and East Africa. Started out as a WhatsApp bot, now it's the FastAPI backend for a standalone Android app built with KivyMD, so there's no WhatsApp dependency anymore.

## What it does

- **AI chat**. Farmers chat with an AI agricultural extension officer (powered by Gemini) that gives advice on crops, pests, diseases, and livestock, tuned to Kenyan/East African context: local crop names, common pests, agro-ecological zones, and so on.
- **Weather and farming insights**. Pulls current conditions and a 7-day forecast for the farmer's location (via Open-Meteo) and generates a short farming tip based on it.
- **Farmer profiles**. Lightweight, device-based identity, no phone number or login required. Farmers can optionally add their name, location, primary crop, and farm size to get more tailored advice.
- **Extension officer directory**. A public directory of real extension officers by county and specialization (crops, livestock, horticulture, agroforestry), so farmers can escalate beyond the AI when needed.
- **Admin analytics**. Key-protected endpoints for basic usage stats: farmer counts, message volume, active farmers in the last 7 days, and top counties.

## Tech stack

- FastAPI (async Python web framework)
- SQLAlchemy 2.0 (async) with aiosqlite / asyncpg. SQLite for local dev, Postgres ready for production
- Google Gemini (google-genai) for chat and weather insight generation
- Open-Meteo for weather (free, no key required)
- Pydantic v2 / pydantic-settings for validation and environment config

## Project structure

```
app/
├── config.py          # Environment-driven settings (.env)
├── database.py         # Async engine, session factory
├── schemas.py          # All Pydantic request/response models
├── models/
│   ├── base.py          # Shared declarative base
│   ├── farmer.py        # Farmer profile (device-based identity)
│   ├── chat.py           # Append-only chat message log
│   └── officer.py        # Extension officer directory
├── routes/
│   ├── farmers.py        # Registration & profile management
│   ├── chat.py            # Chat send / history / clear
│   ├── weather.py          # Weather + AI farming insight
│   ├── officers.py         # Public officer directory + admin CRUD
│   ├── admin.py             # Usage analytics
│   └── deps.py               # Shared auth dependency (admin key)
└── services/
    ├── ai.py              # Gemini prompt-building and calls
    ├── weather.py          # Open-Meteo fetch/parse + geocoding
    ├── farmer.py           # Farmer DB operations
    ├── chat.py             # Chat DB operations
    └── officer.py          # Officer DB operations
main.py       # App factory: CORS, router registration, /health
seed.py       # Seeds sample extension officers into the DB
```

## Getting started

### Prerequisites
- Python 3.11+
- A Google Gemini API key

### Setup

```bash
git clone https://github.com/b100mBUG/AgriCore-Backend.git
cd AgriCore-Backend
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash
ADMIN_API_KEY=choose-a-strong-key
DATABASE_URL=sqlite+aiosqlite:///./agribot.db
ALLOWED_ORIGINS=*
CONTEXT_WINDOW_MESSAGES=10
```

Run the server:

```bash
uvicorn main:app --reload
```

The API runs at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.

Optionally, seed a few sample extension officers:

```bash
python seed.py
```

## API overview

| Endpoint | Method | Description |
|---|---|---|
| `/farmers/register` | POST | Register a farmer by device ID (idempotent) |
| `/farmers/{device_id}` | GET / PATCH | Fetch or update a farmer's profile |
| `/chat` | POST | Send a message, get an AI reply |
| `/chat/{device_id}` | GET / DELETE | Paginated chat history / clear history |
| `/weather/farmer/{device_id}` | GET | Weather + AI farming insight for a farmer's saved location |
| `/weather/coords` | GET | Weather by raw lat/lon |
| `/officers` | GET | Public directory of extension officers |
| `/officers` | POST / PATCH / DELETE | Admin-only officer management |
| `/admin/analytics` | GET | Admin-only usage analytics |
| `/health` | GET | Health check |

Admin-only routes require an `X-Admin-Key` header matching `ADMIN_API_KEY`.

## Notes

- Farmer identity is a locally-generated device UUID. No phone number, no login.
- The AI system prompt is tuned for local crop terminology and Kenyan agricultural context, and formats replies using Kivy BBCode markup (not Markdown) so they render correctly in the mobile app's chat UI.
- It never invents pesticide or drug dosages and won't recommend specific veterinary drugs by brand. It defers to package instructions or a human extension officer instead.