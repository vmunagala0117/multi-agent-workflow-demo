from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.config import get_settings


@lru_cache
def get_azure_chat_model() -> ChatOpenAI:
    settings = get_settings()

    return ChatOpenAI(
        model=settings.azure_openai_deployment,
        base_url=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        use_responses_api=True,
        temperature=1,
    )