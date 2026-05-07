# Model Providers Draft

PolicyLens v0.1 includes an OpenAI-compatible LLM Gateway for provider configuration, connection tests, and basic chat calls. It does not hard-code concrete model names. Users configure the model name, base URL, and API key environment variable.

## Preset Providers

| Provider | Provider key | Env var | Notes |
| --- | --- | --- | --- |
| 阿里云百炼 / 通义千问 / DashScope | `dashscope` | `DASHSCOPE_API_KEY` | Configure model name and OpenAI-compatible base URL |
| 百度千帆 / 文心 / Qianfan | `qianfan` | `QIANFAN_API_KEY` | Configure model name and OpenAI-compatible base URL |
| 腾讯混元 / Hunyuan | `hunyuan` | `HUNYUAN_API_KEY` | Configure model name and OpenAI-compatible base URL |
| 火山方舟 / 豆包 / VolcArk | `volcark` | `VOLCARK_API_KEY` | Configure model name and OpenAI-compatible base URL |
| 智谱 AI / GLM / Zhipu | `zhipu` | `ZHIPU_API_KEY` | Configure model name and OpenAI-compatible base URL |
| DeepSeek | `deepseek` | `DEEPSEEK_API_KEY` | Configure model name and OpenAI-compatible base URL |
| Moonshot / Kimi | `kimi` | `KIMI_API_KEY` | Configure model name and OpenAI-compatible base URL |
| MiniMax | `minimax` | `MINIMAX_API_KEY` | Configure model name and OpenAI-compatible base URL |
| 科大讯飞 / 星火 / Spark | `spark` | `SPARK_API_KEY` | Configure model name and OpenAI-compatible base URL |
| OpenAI-compatible Custom Provider | `openai_compatible_custom` | `CUSTOM_LLM_API_KEY` | User-defined base URL and model name |
| Local Provider / Ollama / vLLM | `local` | none by default | Local OpenAI-compatible runtime, no Authorization header required |

## Configuration Rules

- API key values stay in environment variables, local `.env`, secret managers, or deployment secrets.
- Database provider records store only the env var name, for example `DEEPSEEK_API_KEY`.
- API responses return `api_key_configured=true/false`, never the key value.
- Provider presets can be overridden by database provider records with the same `provider_key`.
- Custom provider records can use any OpenAI-compatible `base_url`.
- Local providers may omit `api_key_env` and send no Authorization header.

## API Surface

- `GET /api/llm/providers` lists presets plus database provider configs.
- `POST /api/llm/providers` creates or updates a provider config.
- `POST /api/llm/providers/{provider_id}/test` performs a real `/chat/completions` call.
- `POST /api/llm/chat` performs a non-streaming chat completion call.

Provider tests and chat calls are not run against real external services in CI. Tests use mocked HTTP transports or monkeypatched gateway responses.

## Current Limitations

- Streaming responses are not implemented.
- Embeddings, RAG, Qdrant writes, policy matching, and report generation are out of scope for Task 07.
- Provider-specific SDKs are intentionally not used; all calls go through the OpenAI-compatible HTTP contract.
- Model profile APIs are not exposed yet, but repository functions exist for later Research Plan execution.
