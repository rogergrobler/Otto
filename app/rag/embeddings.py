from app.llm.factory import get_llm_provider


async def embed_texts(texts: list[str]) -> list[list[float]]:
    provider = get_llm_provider()
    return await provider.embed(texts)
