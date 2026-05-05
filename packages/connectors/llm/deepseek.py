from packages.connectors.llm.base import ProviderAdapter, ProviderMetadata


class DeepSeekAdapter(ProviderAdapter):
    metadata = ProviderMetadata(
        id="deepseek",
        display_name="DeepSeek",
        provider_family="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        aliases=("deepseek",),
    )
