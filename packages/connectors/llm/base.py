from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderMetadata:
    id: str
    display_name: str
    provider_family: str
    api_key_env: str | None
    aliases: tuple[str, ...]
    openai_compatible: bool = True
    local_provider: bool = False


class ProviderAdapter:
    """Minimal adapter contract reserved for the future LLM gateway."""

    metadata: ProviderMetadata

    def __init__(self, *, model_name: str, base_url: str | None = None) -> None:
        self.model_name = model_name
        self.base_url = base_url

    def test_connection(self) -> dict[str, str]:
        return {
            "status": "not_implemented",
            "provider_id": self.metadata.id,
            "message": "v0.1 adapter skeleton does not call external models.",
        }
