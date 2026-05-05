from packages.connectors.llm.base import ProviderAdapter, ProviderMetadata


class KimiAdapter(ProviderAdapter):
    metadata = ProviderMetadata(
        id="kimi",
        display_name="Moonshot / Kimi",
        provider_family="kimi",
        api_key_env="KIMI_API_KEY",
        aliases=("moonshot",),
    )
