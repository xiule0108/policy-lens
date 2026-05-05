# Deployment Draft

PolicyLens v0.1 ships a Docker Compose stack for local and development deployment.

## Services

- `web` runs Next.js
- `api` runs FastAPI
- `worker` runs the Python worker skeleton
- `postgres` reserves relational storage
- `qdrant` reserves vector storage

## Start

If your machine does not have Docker, install Docker Desktop first and make sure the `docker` command is available in your terminal.

```bash
cp .env.example .env
docker compose up --build
```

Apply database migrations safely after services start:

```bash
docker compose exec api alembic upgrade head
```

Do not run destructive database resets in container startup commands. Migrations should be explicit and reviewable.

## Inspect Running Services

```bash
docker compose ps
```

Inspect API logs:

```bash
docker compose logs api
```

Inspect web logs:

```bash
docker compose logs web
```

Stop and remove containers:

```bash
docker compose down
```

Validate Compose syntax without starting services:

```bash
docker compose config
```

CI validates Alembic upgrade, downgrade, and upgrade again against both the local SQLite check database and a real PostgreSQL service container.

To inspect migration state inside the API container:

```bash
docker compose exec api alembic current
docker compose exec api alembic history
```

## Ports

- Web: http://localhost:3000
- API: http://localhost:8000
- PostgreSQL: localhost:5432
- Qdrant: http://localhost:6333

## Production Notes

v0.1 is not production ready. Before production deployment, add:

- HTTPS and reverse proxy configuration
- database migrations
- persistent object storage or MinIO
- authentication and authorization
- secret management
- background queue runtime
- observability and audit logging
- backup policy for PostgreSQL, Qdrant, and object storage
