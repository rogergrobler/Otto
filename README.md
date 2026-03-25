# Otto — Consumer Digital Health Twin Platform

Otto is a subscription-based consumer health platform that gives each user a single, unified view of their health and helps them improve their healthspan.

Built on the Digital Health Twin methodology developed by Roger Grobler, combining blood work, genetics, imaging, wearable data, nutrition tracking, goal-setting, and AI-driven analysis — delivered through a conversational AI interface powered by Anthropic Claude.

**A collaboration between More Good Days (Sean Lunn / Faf du Plessis) × Chronos Capital (Roger Grobler)**

---

## Tech Stack

- **Backend:** Python 3.11+ / FastAPI / SQLAlchemy async
- **Database:** PostgreSQL + pgvector
- **AI:** Anthropic Claude API (Sonnet 4)
- **Auth:** JWT (PyJWT + bcrypt)
- **Storage:** S3-compatible object storage
- **Scheduler:** APScheduler (nudge system)
- **Frontend:** Progressive Web App (mobile-first)

## Getting Started

```bash
# Install dependencies
pip install -e ".[dev]"

# Copy environment config
cp .env.example .env

# Run database migrations
alembic upgrade head

# Seed initial data
python scripts/seed.py

# Start the server
uvicorn app.main:app --reload
```

## Docker

```bash
docker-compose up
```

## Architecture

Otto is structured around a health data repository across 12 domains:
Labs · Genetics · Wearables · Nutrition · Training · Supplements · Body Composition · Imaging · Doctor Visits · Risk Register · Goals · Targets

The AI layer (Otto) uses Claude's tool-use capability to query the user's health repository in real time, ensuring every response is grounded in actual data.

## MVP Phases

- **Phase 1 (Weeks 1–4):** Auth, onboarding, lab PDF OCR, chat with Otto, meal photo nutrition logging, basic goals
- **Phase 2 (Weeks 5–8):** Whoop + Oura sync, training log, genetics upload, supplement tracking, biomarker trends
- **Phase 3 (Weeks 9–12):** Risk engine (Four Horsemen), Health Score, nudge system, health coach portal
- **Phase 4 (Weeks 13+):** More wearables, CGM, partner marketplace, native app
