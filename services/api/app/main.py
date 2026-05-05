from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import analysis, documents, exports, health, llm, policies, projects


app = FastAPI(
    title="PolicyLens API",
    description="v0.1 API skeleton for policy and market research analysis.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(policies.router, prefix="/api/policies", tags=["policies"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(exports.router, prefix="/api/exports", tags=["exports"])
app.include_router(llm.router, prefix="/api/llm", tags=["llm"])
