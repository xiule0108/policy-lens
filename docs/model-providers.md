# Model Providers Draft

PolicyLens reserves a Provider Adapter layer for Chinese and global model providers. v0.1 stores only metadata and mock test responses.

## Preset Providers

| Provider | Env var | Notes |
| --- | --- | --- |
| 阿里云百炼 / 通义千问 / DashScope | `DASHSCOPE_API_KEY` | Model name configured by user |
| 百度千帆 / 文心 / Qianfan | `QIANFAN_API_KEY` | Model name configured by user |
| 腾讯混元 / Hunyuan | `HUNYUAN_API_KEY` | Model name configured by user |
| 火山方舟 / 豆包 / VolcArk | `VOLCARK_API_KEY` | Model name configured by user |
| 智谱 AI / GLM / Zhipu | `ZHIPU_API_KEY` | Model name configured by user |
| DeepSeek | `DEEPSEEK_API_KEY` | Model name configured by user |
| Moonshot / Kimi | `KIMI_API_KEY` | Model name configured by user |
| MiniMax | `MINIMAX_API_KEY` | Model name configured by user |
| 科大讯飞 / 星火 / Spark | `SPARK_API_KEY` | Model name configured by user |
| OpenAI-compatible Custom Provider | user-defined | base URL and model name configured by user |
| Local Provider / Ollama / vLLM | none by default | reserved for local runtimes |

## Design Rules

- Do not hard-code concrete model names.
- Do not store API keys in frontend state or repository files.
- Provider tests should distinguish configuration validation from real external calls.
- LLM outputs must separate original facts, retrieved facts, and model reasoning.

## Future Adapter Shape

Each adapter should expose:

- provider metadata
- configured model name
- optional base URL
- secret reference through environment variable
- capability flags
- connection test
- chat or completion call
- structured output validation
