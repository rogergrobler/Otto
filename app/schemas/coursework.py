import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.client_coursework import AssignmentStatus


class CourseworkCreate(BaseModel):
    title: str
    description: str | None = None
    content: str


class CourseworkResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AssignCourseworkRequest(BaseModel):
    client_ids: list[uuid.UUID]
    ping_telegram: bool = True


class ClientCourseworkResponse(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    coursework_id: uuid.UUID
    status: AssignmentStatus
    assigned_at: datetime
    completed_at: datetime | None
    notes: str | None

    model_config = {"from_attributes": True}
