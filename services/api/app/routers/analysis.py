from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter

from app.schemas.common import AnalysisJob, AnalysisJobRequest

router = APIRouter()


@router.post("/jobs", response_model=AnalysisJob, status_code=202)
def create_analysis_job(payload: AnalysisJobRequest) -> AnalysisJob:
    return AnalysisJob(
        id=f"analysis_{uuid4().hex[:8]}",
        project_id=payload.project_id,
        status="queued",
        analysis_types=payload.analysis_types,
        model_profile=payload.model_profile,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        result_preview={
            "impact_matrix": [
                {
                    "policy_axis": "industrial policy",
                    "market_axis": "supply chain cost",
                    "impact": "mock_medium",
                    "evidence_ids": ["evidence_policy_search_mock"],
                }
            ],
            "fact_boundaries": {
                "original_facts": [],
                "retrieved_facts": [],
                "model_reasoning": "Pending worker execution.",
            },
        },
        evidence=[],
    )


@router.get("/jobs/{job_id}", response_model=AnalysisJob)
def get_analysis_job(job_id: str) -> AnalysisJob:
    return AnalysisJob(
        id=job_id,
        project_id="project_demo_001",
        status="completed_mock",
        analysis_types=["impact_matrix", "market_transmission_chain", "fact_check"],
        model_profile="china_balanced",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        result_preview={
            "impact_matrix": [
                {
                    "policy_axis": "funding guidance",
                    "market_axis": "capital expenditure",
                    "impact": "mock_high",
                    "evidence_ids": ["policy_demo_001_section_02"],
                }
            ],
            "fact_boundaries": {
                "original_facts": ["The uploaded article discusses a policy signal."],
                "retrieved_facts": ["A related policy mock record was retrieved."],
                "model_reasoning": "The analysis is a mock interpretation for v0.1.",
            },
        },
        evidence=[
            {
                "id": "policy_demo_001_section_02",
                "source_type": "policy_original",
                "summary": "Mock cited section from a related policy.",
                "confidence": 0.7,
            }
        ],
    )
