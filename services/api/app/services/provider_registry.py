from __future__ import annotations

import os
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import LLMProvider as LLMProviderModel
from app.repositories.llm_providers import get_provider, list_providers
from app.schemas.common import LLMProvider


PROVIDER_PRESETS: list[dict[str, Any]] = [
    {
        "id": "dashscope",
        "display_name": "阿里云百炼 / 通义千问 / DashScope",
        "provider_family": "dashscope",
        "aliases": ["aliyun_bailian", "qwen"],
        "api_key_env": "DASHSCOPE_API_KEY",
        "openai_compatible": True,
        "notes": "Model name and OpenAI-compatible base URL are supplied by user configuration.",
    },
    {
        "id": "qianfan",
        "display_name": "百度千帆 / 文心 / Qianfan",
        "provider_family": "qianfan",
        "aliases": ["baidu_wenxin", "ernie"],
        "api_key_env": "QIANFAN_API_KEY",
        "openai_compatible": True,
        "notes": "Model name and OpenAI-compatible base URL are supplied by user configuration.",
    },
    {
        "id": "hunyuan",
        "display_name": "腾讯混元 / Hunyuan",
        "provider_family": "hunyuan",
        "aliases": ["tencent_hunyuan"],
        "api_key_env": "HUNYUAN_API_KEY",
        "openai_compatible": True,
        "notes": "Model name and OpenAI-compatible base URL are supplied by user configuration.",
    },
    {
        "id": "volcark",
        "display_name": "火山方舟 / 豆包 / VolcArk",
        "provider_family": "volcark",
        "aliases": ["volcengine_ark", "doubao"],
        "api_key_env": "VOLCARK_API_KEY",
        "openai_compatible": True,
        "notes": "Model name and OpenAI-compatible base URL are supplied by user configuration.",
    },
    {
        "id": "zhipu",
        "display_name": "智谱 AI / GLM / Zhipu",
        "provider_family": "zhipu",
        "aliases": ["glm"],
        "api_key_env": "ZHIPU_API_KEY",
        "openai_compatible": True,
        "notes": "Model name and OpenAI-compatible base URL are supplied by user configuration.",
    },
    {
        "id": "deepseek",
        "display_name": "DeepSeek",
        "provider_family": "deepseek",
        "aliases": ["deepseek"],
        "api_key_env": "DEEPSEEK_API_KEY",
        "openai_compatible": True,
        "notes": "Model name and OpenAI-compatible base URL are supplied by user configuration.",
    },
    {
        "id": "kimi",
        "display_name": "Moonshot / Kimi",
        "provider_family": "kimi",
        "aliases": ["moonshot"],
        "api_key_env": "KIMI_API_KEY",
        "openai_compatible": True,
        "notes": "Model name and OpenAI-compatible base URL are supplied by user configuration.",
    },
    {
        "id": "minimax",
        "display_name": "MiniMax",
        "provider_family": "minimax",
        "aliases": ["abab"],
        "api_key_env": "MINIMAX_API_KEY",
        "openai_compatible": True,
        "notes": "Model name and OpenAI-compatible base URL are supplied by user configuration.",
    },
    {
        "id": "spark",
        "display_name": "科大讯飞 / 星火 / Spark",
        "provider_family": "spark",
        "aliases": ["iflytek_spark"],
        "api_key_env": "SPARK_API_KEY",
        "openai_compatible": True,
        "notes": "Model name and OpenAI-compatible base URL are supplied by user configuration.",
    },
    {
        "id": "openai_compatible_custom",
        "display_name": "OpenAI-compatible Custom Provider",
        "provider_family": "openai_compatible",
        "aliases": ["custom"],
        "api_key_env": "CUSTOM_LLM_API_KEY",
        "openai_compatible": True,
        "notes": "User supplies base URL, API key env var, and model name.",
    },
    {
        "id": "local",
        "display_name": "Local Provider / Ollama / vLLM",
        "provider_family": "local",
        "aliases": ["ollama", "vllm"],
        "api_key_env": None,
        "openai_compatible": True,
        "local_provider": True,
        "notes": "Reserved for local OpenAI-compatible runtimes.",
    },
]


def get_provider_presets() -> list[LLMProvider]:
    return [_schema_from_dict(item) for item in PROVIDER_PRESETS]


def list_provider_configs(session: Session) -> list[LLMProvider]:
    providers_by_key = {provider.id: provider for provider in get_provider_presets()}
    for user_provider in list_providers(session):
        preset = providers_by_key.get(user_provider.provider_key)
        providers_by_key[user_provider.provider_key] = merge_preset_and_user_provider(preset, user_provider)
    return sorted(providers_by_key.values(), key=lambda provider: provider.id)


def get_provider_config(session: Session, provider_key: str) -> LLMProvider | None:
    preset = next((provider for provider in get_provider_presets() if provider.id == provider_key), None)
    user_provider = get_provider(session, provider_key)
    if user_provider is None:
        return preset
    return merge_preset_and_user_provider(preset, user_provider)


def merge_preset_and_user_provider(
    preset: LLMProvider | None,
    user_provider: LLMProviderModel,
) -> LLMProvider:
    config = user_provider.config or {}
    api_key_env = user_provider.api_key_env
    local_provider = bool(config.get("local_provider", preset.local_provider if preset else False))
    return LLMProvider(
        id=user_provider.provider_key,
        display_name=user_provider.display_name or (preset.display_name if preset else user_provider.provider_key),
        provider_family=user_provider.provider_type or (preset.provider_family if preset else "openai_compatible"),
        aliases=list(config.get("aliases", preset.aliases if preset else [])),
        api_key_env=api_key_env,
        api_key_configured=_api_key_configured(api_key_env),
        base_url=user_provider.base_url if user_provider.base_url is not None else (preset.base_url if preset else None),
        model_name=config.get("model_name", preset.model_name if preset else None),
        enabled=user_provider.enabled,
        openai_compatible=bool(config.get("openai_compatible", preset.openai_compatible if preset else True)),
        local_provider=local_provider,
        notes=config.get("notes") or (preset.notes if preset else "User-created provider config."),
    )


def _schema_from_dict(data: dict[str, Any]) -> LLMProvider:
    api_key_env = data.get("api_key_env")
    return LLMProvider(
        id=data["id"],
        display_name=data["display_name"],
        provider_family=data["provider_family"],
        aliases=list(data.get("aliases", [])),
        api_key_env=api_key_env,
        api_key_configured=_api_key_configured(api_key_env),
        base_url=data.get("base_url"),
        model_name=data.get("model_name"),
        enabled=data.get("enabled", False),
        openai_compatible=data.get("openai_compatible", False),
        local_provider=data.get("local_provider", False),
        notes=data.get("notes"),
    )


def _api_key_configured(api_key_env: str | None) -> bool:
    if not api_key_env:
        return False
    return bool(os.environ.get(api_key_env))
