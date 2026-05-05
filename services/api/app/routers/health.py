from fastapi import APIRouter

from app.db.session import get_database_status
from app.schemas.common import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="policy-lens-api",
        version="0.1.0",
        dependencies={
            "database": get_database_status(),
            "vector_store": {"status": "not_connected", "mode": "v0.1_mock"},
            "storage": {"status": "local_reserved", "mode": "v0.1_mock"},
        },
    )
