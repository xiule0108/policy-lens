from packages.connectors.llm.base import ProviderAdapter, ProviderMetadata


class QianfanAdapter(ProviderAdapter):
    metadata = ProviderMetadata(
        id="qianfan",
        display_name="百度千帆 / 文心 / Qianfan",
        provider_family="qianfan",
        api_key_env="QIANFAN_API_KEY",
        aliases=("baidu_wenxin", "ernie"),
    )
