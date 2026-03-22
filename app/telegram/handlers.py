import logging

from sqlalchemy import select
from telegram import Update
from telegram.ext import ContextTypes

from app.db.session import async_session
from app.engine.coaching_engine import process_message
from app.models.client import Client
from app.models.conversation import Channel

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id

    async with async_session() as db:
        result = await db.execute(
            select(Client).where(Client.telegram_chat_id == chat_id)
        )
        client = result.scalars().first()

        if client:
            await update.message.reply_text(
                f"Welcome back, {client.full_name}! I'm Sofia, your coaching assistant. "
                "How can I support you today?"
            )
        else:
            # Try to match by username
            username = update.effective_user.username
            if username:
                result = await db.execute(
                    select(Client).where(Client.telegram_username == username)
                )
                client = result.scalars().first()
                if client:
                    client.telegram_chat_id = chat_id
                    await db.commit()
                    await update.message.reply_text(
                        f"Hi {client.full_name}! I've linked your Telegram account. "
                        "I'm Sofia, your coaching assistant. How can I support you today?"
                    )
                    return

            await update.message.reply_text(
                "Hi there! I'm Sofia, an AI coaching assistant. "
                "It looks like you haven't been registered yet. "
                "Please ask your coach to set up your account, and then come back!"
            )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    text = update.message.text

    if not text:
        return

    async with async_session() as db:
        result = await db.execute(
            select(Client).where(
                Client.telegram_chat_id == chat_id, Client.is_active.is_(True)
            )
        )
        client = result.scalars().first()

        if not client:
            await update.message.reply_text(
                "I don't have you registered yet. Please use /start or ask your coach "
                "to set up your account."
            )
            return

        try:
            response = await process_message(db, client, text, Channel.TELEGRAM)
            await db.commit()
            await update.message.reply_text(response)
        except Exception:
            logger.exception("Error processing message for client %s", client.id)
            await update.message.reply_text(
                "I'm sorry, I'm having a moment of technical difficulty. "
                "Please try again in a few minutes, or reach out to your coach directly."
            )
