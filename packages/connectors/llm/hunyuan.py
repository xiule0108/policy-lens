from packages.connectors.llm.base import ProviderAdapter, ProviderMetadata


class HunyuanAdapter(ProviderAdapter):
    metadata = ProviderMetadata(
        id="hunyuan",
        display_name="腾讯混元 / Hunyuan",
        provider_family="hunyuan",
        api_key_env="HUNYUAN_API_KEY",
        aliases=("tencent_hunyuan",),
    )
