from packages.connectors.llm.base import ProviderAdapter, ProviderMetadata


class OpenAICompatibleAdapter(ProviderAdapter):
    metadata = ProviderMetadata(
        id="openai_compatible_custom",
        display_name="OpenAI-compatible Custom Provider",
        provider_family="openai_compatible",
        api_key_env=None,
        aliases=("custom",),
        openai_compatible=True,
    )
