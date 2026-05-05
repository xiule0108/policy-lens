from packages.connectors.llm.base import ProviderAdapter, ProviderMetadata


class SparkAdapter(ProviderAdapter):
    metadata = ProviderMetadata(
        id="spark",
        display_name="科大讯飞 / 星火 / Spark",
        provider_family="spark",
        api_key_env="SPARK_API_KEY",
        aliases=("iflytek_spark",),
    )
