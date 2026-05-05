# Installation Draft

This document covers v0.1 local setup for PolicyLens / 政研透镜.

## Requirements

- Docker and Docker Compose for full local stack
- Node.js 22 or newer for frontend development
- Python 3.11 or newer for backend development

## Environment

Create a local environment file when needed:

```bash
cp .env.example .env
```

Do not put real credentials into committed files. API keys should stay in local `.env`, a secret manager, or deployment-specific secret storage.

## API Setup

```bash
cd services/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
PYTHONPATH=../..:. uvicorn app.main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/api/health
```

## Web Setup

```bash
cd apps/web
npm install
npm run dev
```

Open http://localhost:3000.

## Worker Setup

```bash
cd services/worker
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m app.main
```

The worker is a placeholder loop in v0.1.
