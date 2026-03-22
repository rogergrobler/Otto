import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class ClientCreate(BaseModel):
    full_name: str
    email: EmailStr | None = None
    password: str | None = None
    telegram_username: str | None = None
    notes: str | None = None


class ClientUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    telegram_username: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class ClientResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str | None
    telegram_chat_id: int | None
    telegram_username: str | None
    notes: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ClientDetailResponse(ClientResponse):
    memory_summary: str | None
    updated_at: datetime
