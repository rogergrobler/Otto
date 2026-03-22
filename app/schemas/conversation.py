import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.conversation import Channel


class ConversationResponse(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    channel: Channel
    started_at: datetime
    ended_at: datetime | None
    summary: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
