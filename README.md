# PolicyLens / 政研透镜

PolicyLens 是一个开源的政策与市场研究解析工作台。项目面向政策研究、市场研究、行业研究和投研分析场景，目标是让用户上传研究文章后，能够解析文章、检索关联政策、查看并导出政策原文、生成政策影响矩阵、生成研究报告，并接入中国及全球主流大模型。

当前仓库处于 v0.1 engineering scaffold 阶段，重点是把 monorepo、开发规范、Docker 服务、API 骨架、前端骨架、数据库底座和模型 Provider 预设跑通。v0.1 release target 是跑通上传文章、政策入库、政策原文导出、基础检索、基础分析和报告导出的最小闭环。

## Core Features

- 研究项目管理和文章上传入口
- 政策关联检索和政策库浏览骨架
- 政策原文导出包骨架，保留来源、时间戳和 sha256 设计
- 政策影响矩阵、市场传导链、事实核查和图谱工作台页面
- 研究报告导出 API 骨架
- 中国主流大模型和 OpenAI-compatible Provider 接入预设

## v0.1 Scope And Roadmap

当前提交提供可运行工程骨架和数据库基础设施：

- Next.js 前端页面使用 mock 数据
- FastAPI API 提供 mock 业务结构，并已轻度接入 projects、exports、LLM user providers 的数据库持久化
- PostgreSQL schema、SQLAlchemy models、Alembic migration 和 repository 层已经建立
- Qdrant、worker 和本地存储仍以服务预留为主
- LLM Gateway 只完成 Provider 配置和测试接口骨架
- 政策原文导出只完成 bundle 目录结构和 manifest skeleton

当前提交暂未实现真实文件解析、完整检索、rerank、向量化、真实模型调用、报告生成和生产级任务队列；这些属于 v0.1 release roadmap。权限系统和政策来源自动抓取可后续迭代。

## Tech Stack

- Monorepo
- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Backend: FastAPI, Python
- Database: PostgreSQL
- Vector DB: Qdrant
- Object Storage: local filesystem, MinIO reserved
- Worker: Python worker skeleton
- LLM Gateway: LiteLLM / OpenAI-compatible adapter reserved
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
The script also validates Alembic upgrade, downgrade, and upgrade again against a local SQLite check database.

## CI Status

GitHub Actions CI is defined in `.github/workflows/ci.yml`. After the repository is pushed to GitHub, check the Actions tab for the `CI` workflow status. The workflow validates:

- backend tests
- Alembic migration upgrade, downgrade, and upgrade
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

The project does not hard-code concrete model names. Users configure model IDs and credentials through environment variables or future UI settings.

## Policy Original Export

The policy original exporter is designed to package traceable policy evidence:

```text
policy_export_bundle.zip
  manifest.json
  policies/
  cited_sections/
  snapshots/
  mappings/
  checksums/
```

Planned export modes:

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
