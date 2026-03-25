import base64

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.dependencies import get_current_client
from app.engine.coaching_engine import process_message
from app.models.client import Client
from app.models.conversation import Channel

router = APIRouter(prefix="/chat", tags=["voice"])


@router.post("/voice")
async def voice_message(
    audio: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="Voice not configured")

    openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    audio_bytes = await audio.read()

    # Transcribe with Whisper
    try:
        transcript = await openai.audio.transcriptions.create(
            model="whisper-1",
            file=(audio.filename or "recording.webm", audio_bytes, audio.content_type or "audio/webm"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

    user_text = transcript.text.strip()
    if not user_text:
        raise HTTPException(status_code=422, detail="No speech detected")

    # Process through existing coaching pipeline
    response_text = await process_message(db, client, user_text, Channel.WEB)

    # Synthesize speech - OpenAI fable voice (warm British accent)
    audio_data = None
    try:
        tts = await openai.audio.speech.create(
            model="tts-1-hd",
            voice="fable",
            input=response_text,
            response_format="mp3",
        )
        audio_data = base64.b64encode(tts.content).decode()
    except Exception:
        pass  # Return text response even if TTS fails

    return JSONResponse({
        "transcript": user_text,
        "response": response_text,
        "audio": audio_data,
    })

