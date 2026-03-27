import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.config import settings
from app.tasks.nudge_scheduler import create_scheduler

logging.basicConfig(
    level=logging.DEBUG if settings.APP_ENV == "development" else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Otto Digital Health Twin")

    # Initialize Telegram bot
    from app.telegram.bot import setup_bot, shutdown_bot

    await setup_bot()

    # Start nudge scheduler
    scheduler = create_scheduler()
    scheduler.start()
    logger.info("Nudge scheduler started")

    yield

    # Shutdown
    scheduler.shutdown(wait=False)
    await shutdown_bot()
    logger.info("Otto shutting down")


app = FastAPI(
    title="Otto — Digital Health Twin",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def index():
    return FileResponse(str(static_dir / "chat.html"))


@app.get("/health")
async def health():
    return {"status": "ok", "service": "otto"}
