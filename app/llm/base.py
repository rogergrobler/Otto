from typing import Protocol


class LLMProvider(Protocol):
    """Abstract interface for LLM providers."""

    async def chat(
        self,
        messages: list[dict],
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Send messages and get a response.

        Args:
            messages: List of {"role": "user"|"assistant", "content": "..."}.
            system: Optional system prompt (handled differently per provider).
            model: Override the default model.
            max_tokens: Maximum tokens in the response.
            temperature: Sampling temperature.

        Returns:
            The assistant's response text.
        """
        ...

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        ...
