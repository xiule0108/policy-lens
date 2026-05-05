from fastapi import APIRouter

from app.schemas.common import PolicyListResponse, PolicySearchRequest, PolicySearchResponse
from app.services.mock_data import mock_policies

router = APIRouter()


@router.get("", response_model=PolicyListResponse)
def list_policies() -> PolicyListResponse:
    return PolicyListResponse(items=mock_policies())


@router.post("/search", response_model=PolicySearchResponse)
def search_policies(payload: PolicySearchRequest) -> PolicySearchResponse:
    policies = mock_policies()
    return PolicySearchResponse(
        query=payload.query,
        total=len(policies),
        items=policies,
        evidence=[
            {
                "id": "evidence_policy_search_mock",
                "source_type": "policy_index",
                "summary": "Mock hybrid search result. Replace with keyword, vector, and rerank pipeline.",
                "confidence": 0.62,
            }
        ],
    )
