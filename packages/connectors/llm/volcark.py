from packages.connectors.llm.base import ProviderAdapter, ProviderMetadata


class VolcArkAdapter(ProviderAdapter):
    metadata = ProviderMetadata(
        id="volcark",
        display_name="火山方舟 / 豆包 / VolcArk",
        provider_family="volcark",
        api_key_env="VOLCARK_API_KEY",
        aliases=("volcengine_ark", "doubao"),
    )
