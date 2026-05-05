from packages.connectors.llm.base import ProviderAdapter, ProviderMetadata


class DashScopeAdapter(ProviderAdapter):
    metadata = ProviderMetadata(
        id="dashscope",
        display_name="阿里云百炼 / 通义千问 / DashScope",
        provider_family="dashscope",
        api_key_env="DASHSCOPE_API_KEY",
        aliases=("aliyun_bailian", "qwen"),
    )
