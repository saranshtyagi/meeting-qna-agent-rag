from langchain_mistralai import ChatMistralAI

from app.config import settings


def get_llm(temperature: float = 0.3):
    """
    Factory for creating Mistral LLM instances.

    Centralizing LLM creation means changing models,
    temperatures, or providers only requires updating
    this file.
    """

    return ChatMistralAI(
        model=settings.MISTRAL_MODEL,
        mistral_api_key=settings.MISTRAL_API_KEY,
        temperature=temperature,
    )