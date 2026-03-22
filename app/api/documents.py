import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_admin
from app.models.document import DocType, Document
from app.models.user import User
from app.rag.chunker import chunk_document
from app.rag.vector_store import add_chunks, delete_document_chunks
from app.schemas.document import DocumentResponse

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = Path("uploads")


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    result = await db.execute(
        select(Document).where(Document.is_active.is_(True)).order_by(Document.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    doc_type: DocType = Form(...),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    # Save file
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_id = str(uuid.uuid4())
    suffix = Path(file.filename).suffix if file.filename else ".txt"
    file_path = UPLOAD_DIR / f"{file_id}{suffix}"

    content = await file.read()
    file_path.write_bytes(content)

    # Create document record
    doc = Document(
        title=title,
        doc_type=doc_type,
        file_path=str(file_path),
        uploaded_by_id=admin.id,
    )
    db.add(doc)
    await db.flush()

    # Chunk and index
    chunks = chunk_document(str(file_path))
    collection_name = doc_type.value
    await add_chunks(
        collection_name=collection_name,
        chunks=chunks,
        document_id=str(doc.id),
        metadata={"title": title, "doc_type": doc_type.value},
    )

    return doc


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    doc.is_active = False
    await delete_document_chunks(doc.doc_type.value, str(doc.id))
    await db.flush()


@router.post("/{document_id}/reindex", status_code=status.HTTP_200_OK)
async def reindex_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Delete old chunks and re-index
    await delete_document_chunks(doc.doc_type.value, str(doc.id))
    chunks = chunk_document(doc.file_path)
    await add_chunks(
        collection_name=doc.doc_type.value,
        chunks=chunks,
        document_id=str(doc.id),
        metadata={"title": doc.title, "doc_type": doc.doc_type.value},
    )
    return {"status": "reindexed", "chunks": len(chunks)}
