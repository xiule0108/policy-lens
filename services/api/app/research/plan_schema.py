from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ResearchPlanStep(BaseModel):
    step_id: str
    name: str
    tool_name: str
    description: str
    depends_on: list[str] = Field(default_factory=list)
    input_ref: dict[str, Any] = Field(default_factory=dict)
    output_key: str
    model_profile: str | None = None
    required: bool = True


class ResearchPlan(BaseModel):
    plan_id: str
    project_id: str
    document_id: str
    mode: str
    model_profile: str | None = None
    created_at: datetime
    steps: list[ResearchPlanStep]
    metadata: dict[str, Any] = Field(default_factory=dict)


@dataclass(frozen=True)
class StepRunResult:
    output_ref: dict[str, Any]
    token_usage: dict[str, Any] = field(default_factory=dict)
    model_provider: str | None = None
    model_name: str | None = None
