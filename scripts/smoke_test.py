from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.observability.logging_config import configure_logging


def main() -> None:
    configure_logging()
    settings = get_settings()

    model = ChatOpenAI(
        model=settings.azure_openai_deployment,
        base_url=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        use_responses_api=True,
        temperature=1,
    )

    response = model.invoke(
        "Reply with exactly: MedEvidence model connection successful"
    )

    print(response.text)


if __name__ == "__main__":
    main()