import logging

from telegram.ext import Application, MessageHandler, filters

from app.config import settings
from app.telegram.handlers import handle_message, start_command

logger = logging.getLogger(__name__)

_application: Application | None = None


async def setup_bot() -> Application | None:
    global _application

    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set, skipping Telegram bot setup")
        return None

    _application = (
        Application.builder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .updater(None)  # We handle updates via webhook
        .build()
    )

    # Register handlers
    from telegram.ext import CommandHandler

    _application.add_handler(CommandHandler("start", start_command))
    _application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await _application.initialize()
    logger.info("Telegram bot initialized")
    return _application


async def shutdown_bot() -> None:
    global _application
    if _application:
        await _application.shutdown()
        _application = None


def get_application() -> Application | None:
    return _application


async def send_message(chat_id: int, text: str) -> None:
    if _application is None:
        raise RuntimeError("Telegram bot not initialized")
    await _application.bot.send_message(chat_id=chat_id, text=text)
