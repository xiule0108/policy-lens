# PolicyLens / 政研透镜

PolicyLens 是一个开源的政策与市场研究解析工作台。项目面向政策研究、市场研究、行业研究和投研分析场景，目标是让用户上传研究文章后，能够解析文章、检索关联政策、查看并导出政策原文、生成政策影响矩阵、生成研究报告，并接入中国及全球主流大模型。

当前仓库处于 v0.1 engineering scaffold 阶段，重点是把 monorepo、开发规范、Docker 服务、API 骨架、前端骨架、数据库底座和模型 Provider 预设跑通。v0.1 release target 是跑通上传文章、政策入库、政策原文导出、基础检索、基础分析和报告导出的最小闭环。

## Core Features

- 研究项目管理和文章上传入口
- 政策关联检索和政策库浏览骨架
- 政策原文 ZIP 导出，保留来源、时间戳和 sha256 checksum
- 政策影响矩阵、市场传导链、事实核查和图谱工作台页面
- 研究报告导出 API 骨架
- 中国主流大模型和 OpenAI-compatible Provider 配置、连接测试和基础 chat 调用

## v0.1 Scope And Roadmap

当前提交提供可运行工程骨架和数据库基础设施：

- Next.js 前端页面使用 mock 数据
- FastAPI API 提供 mock 业务结构，并已接入 projects、documents、document_chunks、policies、policy_versions、policy_sections、exports、LLM user providers 的数据库持久化
- PostgreSQL schema、SQLAlchemy models、Alembic migration 和 repository 层已经建立
- 本地文件上传、基础文档解析、chunk 入库、政策入库和政策原文 ZIP 导出已经跑通
- Qdrant 和 worker 仍以服务预留为主
- LLM Gateway 已支持 OpenAI-compatible chat 调用、Provider 连接测试和不落库密钥读取
- 政策原文导出已经支持本地 ZIP bundle、manifest 和 sha256 checksums

当前提交暂未实现 OCR、完整检索、rerank、向量化、streaming、报告生成和生产级任务队列；这些属于 v0.1 release roadmap。权限系统和政策来源自动抓取可后续迭代。

## Tech Stack

- Monorepo
- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Backend: FastAPI, Python
- Database: PostgreSQL
- Vector DB: Qdrant
- Object Storage: local filesystem, MinIO reserved
- Worker: Python worker skeleton
- LLM Gateway: OpenAI-compatible provider adapter, LiteLLM reserved
- Deployment: Docker Compose

## Local Development

Start the API locally:

```bash
cd policy-lens/services/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Set `DATABASE_URL` when using a database other than the default local PostgreSQL URL:

```bash
export DATABASE_URL=postgresql://policylens:policylens@localhost:5432/policylens
```

Configure local upload storage when needed:

```bash
export STORAGE_DIR=./storage
export MAX_UPLOAD_SIZE_MB=50
export ALLOWED_UPLOAD_EXTENSIONS=.pdf,.docx,.txt,.md,.markdown,.html,.htm
export CHUNK_MAX_CHARS=2000
```

Configure model provider secrets through environment variables only:

```bash
export DEEPSEEK_API_KEY=...
export CUSTOM_LLM_API_KEY=...
```

Provider records store the environment variable name, base URL, and user-chosen model name. They never store or return the API key value.

Start the web app locally:

```bash
cd policy-lens/apps/web
npm install
npm run dev
```

Then open:

- Web: http://localhost:3000
- API health: http://localhost:8000/api/health
- API docs: http://localhost:8000/docs

## Docker Compose

Copy the environment template if you want local overrides:

```bash
cd policy-lens
cp .env.example .env
docker compose up --build
```

Apply database migrations after the services are running:

```bash
docker compose exec api alembic upgrade head
```

Services:

- web: http://localhost:3000
- api: http://localhost:8000
- postgres: localhost:5432
- qdrant: http://localhost:6333

## Development Validation

Run the local validation script before opening a pull request:

```bash
cd policy-lens
bash scripts/check.sh
```

The script runs backend tests, frontend type checks, and frontend production build. It does not require Docker.
If no Python virtual environment is active, the script creates `services/api/.venv` locally.
The script also validates Alembic upgrade, downgrade, and upgrade again against a local SQLite check database. GitHub Actions additionally validates the same migration cycle against PostgreSQL.

## Document Uploads

`POST /api/documents/upload` accepts `multipart/form-data` with `project_id`, `document_role`, optional `title`, optional `source_url`, and a required `file` part. Supported roles are `research_article`, `policy`, and `appendix`.

Uploaded files are stored under the configured `STORAGE_DIR` using this relative key pattern:

```text
documents/{project_id}/{document_id}/{safe_filename}
```

The API stores only the relative `storage_key` in the database, along with file size, file type, content type metadata, source URL, sha256, and `parse_status=pending`.

Uploads support Unicode filenames, including Chinese policy filenames. The server stores a safe filename for local storage and keeps `metadata.original_filename` plus `metadata.safe_filename` on the document record.

## Document Parsing

`POST /api/documents/{document_id}/parse` synchronously runs the v0.1 basic parser for uploaded `.txt`, `.md`, `.markdown`, `.html`, `.htm`, `.docx`, and searchable `.pdf` files. It does not run OCR, so scanned PDFs without extractable text return a parse failure.

Parsing moves documents through these statuses:

```text
pending -> parsing -> parsed
pending -> parsing -> failed
```

Successful parses write deterministic chunks into `document_chunks` with sequential `chunk_index`, page and section metadata when available, rough `token_count`, and `metadata.parse_summary` on the document. Re-parsing deletes old chunks before writing the new set. `GET /api/documents/{document_id}/chunks` returns stored chunks with `limit` and `offset`. Chunk size defaults to `CHUNK_MAX_CHARS=2000`.

## Policy Library

`POST /api/policies/from-document` ingests an already parsed `document_role=policy` document into the local policy library. The source document must have `parse_status=parsed`, a `storage_key`, and at least one `document_chunks` row.

Ingestion creates:

- `policies`: policy metadata such as title, issuer, jurisdiction, type, dates, status, source URL, and source document sha256
- `policy_versions`: current policy text assembled from document chunks, with normalized text sha256 and source document metadata
- `policy_sections`: one section per source chunk, preserving source chunk id, chunk index, page range, section title, content type, and token estimate

The policy library API is database-backed:

- `GET /api/policies`
- `POST /api/policies/search`
- `GET /api/policies/{policy_id}`
- `GET /api/policies/{policy_id}/versions`
- `GET /api/policies/{policy_id}/sections`
- `GET /api/policies/{policy_id}/original`

Repeated ingestion of the same document returns the existing policy/version by default. Set `force_new_version=true` to create a new current version for the same policy and mark older versions as not current.

This local policy library does not crawl policy sources, judge legal validity, run policy relevance analysis, or call LLMs.

## Policy Original Export

`POST /api/exports/policy-originals` creates a real ZIP bundle from local policy library records. It reads `policies`, the current `policy_versions`, and `policy_sections`, then writes the bundle below `STORAGE_DIR` using a relative database key:

```text
exports/{export_id}/policy_export_bundle.zip
```

Supported modes:

- `single_policy_full_text`
- `related_policy_bundle`
- `cited_sections_only`
- `evidence_bundle`
- `machine_readable_json`

Supported policy file formats are `markdown`, `txt`, `html`, and `json`. The bundle includes `manifest.json` and, by default, `checksums/sha256.txt`. Use `GET /api/exports/{export_id}` to inspect status and `GET /api/exports/{export_id}/download` to download the ZIP.

The v0.1 exporter packages normalized policy text and sections from the database. It does not copy user-uploaded source files into the ZIP and does not include original web/PDF snapshots yet; `manifest.json` records `snapshot_status=not_available_in_v0.1` when snapshots are requested.

## CI Status

GitHub Actions CI is defined in `.github/workflows/ci.yml`. After the repository is pushed to GitHub, check the Actions tab for the `CI` workflow status. The workflow validates:

- backend tests
- Alembic migration upgrade, downgrade, and upgrade against SQLite
- Alembic migration upgrade, downgrade, and upgrade against PostgreSQL
- frontend typecheck and build
- Docker Compose configuration syntax

## How To Report Bugs

Use the bug report issue template and include environment, reproduction steps, expected behavior, actual behavior, logs, and screenshots when relevant.

## How To Request Features

Use the feature request issue template and include the feature goal, usage scenario, suggested approach, data or policy sources, and acceptance criteria.

## Directory Structure

```text
policy-lens/
  apps/web/                 Next.js frontend
  services/api/             FastAPI service
  services/worker/          Python worker skeleton
  packages/core/            shared research and citation primitives
  packages/parsers/         parser package placeholders
  packages/retrievers/      search, rerank, and vector store placeholders
  packages/connectors/      LLM, policy source, and storage connectors
  packages/exporters/       report, policy original, and evidence exporters
  packages/prompts/         zh/en prompt assets
  packages/evals/           fixtures and golden cases
  infra/                    docker, migrations, nginx placeholders
  docs/                     project documentation
```

## Model Provider Plan

PolicyLens will support user-configured model names across these Provider families:

- 阿里云百炼 / 通义千问 / DashScope
- 百度千帆 / 文心 / Qianfan
- 腾讯混元 / Hunyuan
- 火山方舟 / 豆包 / VolcArk
- 智谱 AI / GLM / Zhipu
- DeepSeek
- Moonshot / Kimi
- MiniMax
- 科大讯飞 / 星火 / Spark
- OpenAI-compatible Custom Provider
- Local Provider / Ollama / vLLM

The project does not hard-code concrete model names. Users configure model IDs, OpenAI-compatible base URLs, and credential environment variable names through the API or future UI settings. `POST /api/llm/providers/{provider_id}/test` and `POST /api/llm/chat` make real OpenAI-compatible calls when a provider has `base_url`, `model_name`, and either a configured API key env var or `local_provider=true`.

## Policy Original Export Guarantees

The policy original exporter packages traceable policy evidence:

```text
policy_export_bundle.zip
  manifest.json
  policies/
  cited_sections/
  evidence/
  machine_readable/
  checksums/
```

Supported export modes:

- single_policy_full_text
- related_policy_bundle
- cited_sections_only
- evidence_bundle
- machine_readable_json

Every exported policy original must retain source URL or source identifier, retrieval timestamp, content timestamp when available, and sha256 checksum.

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md) before opening issues, pull requests, or AI-agent generated changes.

## Disclaimer

PolicyLens is a research aid, not legal, investment, policy compliance, or financial advice. Generated analysis must be reviewed by qualified humans. Policy sources, citations, timestamps, and checksums should be preserved so downstream users can verify conclusions against original materials.
