from __future__ import annotations

import uuid

import chromadb

from app.config import settings
from app.rag.embeddings import embed_texts

_client: chromadb.HttpClient | None = None


def get_chroma_client() -> chromadb.HttpClient:
    global _client
    if _client is None:
        _client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
    return _client


def get_collection(name: str) -> chromadb.Collection:
    client = get_chroma_client()
    return client.get_or_create_collection(name=name)


async def add_chunks(
    collection_name: str,
    chunks: list[str],
    document_id: str,
    metadata: dict | None = None,
) -> None:
    if not chunks:
        return

    collection = get_collection(collection_name)
    embeddings = await embed_texts(chunks)

    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = []
    for i, chunk in enumerate(chunks):
        meta = {"document_id": document_id, "chunk_index": i}
        if metadata:
            meta.update(metadata)
        metadatas.append(meta)

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )


async def query_chunks(
    collection_name: str,
    query: str,
    n_results: int = 5,
    where: dict | None = None,
) -> list[dict]:
    collection = get_collection(collection_name)
    query_embedding = await embed_texts([query])

    kwargs: dict = {
        "query_embeddings": query_embedding,
        "n_results": n_results,
    }
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)

    items = []
    if results["documents"]:
        for i, doc in enumerate(results["documents"][0]):
            items.append({
                "content": doc,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else None,
            })
    return items


async def delete_document_chunks(collection_name: str, document_id: str) -> None:
    collection = get_collection(collection_name)
    collection.delete(where={"document_id": document_id})
