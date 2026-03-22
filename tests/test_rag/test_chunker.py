from app.rag.chunker import chunk_text


def test_chunk_text_short():
    text = "This is a short text."
    chunks = chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_long():
    text = "word " * 500  # ~2500 chars
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) > 1
    # Each chunk should be <= chunk_size
    for chunk in chunks:
        assert len(chunk) <= 550  # Allow some tolerance for word boundaries
