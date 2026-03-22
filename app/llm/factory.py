from app.config import settings
from app.llm.base import LLMProvider
from app.llm.claude import ClaudeLLM
from app.llm.openai_provider import OpenAILLM

_instance: LLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    global _instance
    if _instance is None:
        if settings.LLM_PROVIDER == "openai":
            _instance = OpenAILLM()
        else:
            _instance = ClaudeLLM()
    return _instance
