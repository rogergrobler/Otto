from fastapi import APIRouter

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.clients import router as clients_router
from app.api.conversations import router as conversations_router
from app.api.coursework import router as coursework_router
from app.api.documents import router as documents_router
from app.api.telegram_webhook import router as telegram_router
from app.api.voice import router as voice_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(clients_router)
api_router.include_router(conversations_router)
api_router.include_router(chat_router)
api_router.include_router(voice_router)
api_router.include_router(documents_router)
api_router.include_router(coursework_router)
api_router.include_router(admin_router)
api_router.include_router(telegram_router)

