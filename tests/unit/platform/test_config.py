from app.config import Settings


def test_settings_can_be_constructed_explicitly() -> None:
    settings = Settings(
        azure_openai_endpoint="https://example.openai.azure.com/",
        azure_openai_api_key="test-key",
        azure_openai_api_version="2024-10-21",
        azure_openai_deployment="test-deployment",
    )

    assert settings.azure_openai_deployment == "test-deployment"
    assert settings.app_env == "local"
