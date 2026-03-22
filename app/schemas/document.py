import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.document import DocType


class DocumentResponse(BaseModel):
    id: uuid.UUID
    title: str
    doc_type: DocType
    file_path: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
