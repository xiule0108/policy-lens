from packages.connectors.llm.base import ProviderAdapter, ProviderMetadata


class ZhipuAdapter(ProviderAdapter):
    metadata = ProviderMetadata(
        id="zhipu",
        display_name="智谱 AI / GLM / Zhipu",
        provider_family="zhipu",
        api_key_env="ZHIPU_API_KEY",
        aliases=("glm",),
    )
