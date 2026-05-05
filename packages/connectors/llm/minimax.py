from packages.connectors.llm.base import ProviderAdapter, ProviderMetadata


class MiniMaxAdapter(ProviderAdapter):
    metadata = ProviderMetadata(
        id="minimax",
        display_name="MiniMax",
        provider_family="minimax",
        api_key_env="MINIMAX_API_KEY",
        aliases=("abab",),
    )
