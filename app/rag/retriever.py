from app.rag.vector_store import query_chunks


async def retrieve_context(
    query: str,
    collection_names: list[str] | None = None,
    n_results: int = 5,
    where: dict | None = None,
) -> str:
    if collection_names is None:
        collection_names = ["methodology", "coursework"]

    all_chunks = []
    for collection_name in collection_names:
        try:
            chunks = await query_chunks(
                collection_name=collection_name,
                query=query,
                n_results=n_results,
                where=where,
            )
            all_chunks.extend(chunks)
        except Exception:
            # Collection may not exist yet
            continue

    # Sort by distance (lower is more relevant)
    all_chunks.sort(key=lambda c: c.get("distance", float("inf")))

    # Take top n_results across all collections
    top_chunks = all_chunks[:n_results]

    if not top_chunks:
        return ""

    parts = ["## Relevant Knowledge Base Context"]
    for chunk in top_chunks:
        parts.append(chunk["content"])

    return "\n\n---\n\n".join(parts)
