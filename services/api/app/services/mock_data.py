from datetime import datetime, timezone

from app.schemas.common import Document, EvidenceItem, Policy, Project, SourceRef


def mock_source(source_id: str, title: str, url: str) -> SourceRef:
    return SourceRef(
        id=source_id,
        title=title,
        url=url,
        publisher="PolicyLens mock source",
        retrieved_at=datetime.now(timezone.utc),
        sha256="0" * 64,
    )


def mock_projects() -> list[Project]:
    now = datetime.now(timezone.utc)
    return [
        Project(
            id="project_demo_001",
            name="新能源产业政策影响研究",
            description="Mock project for policy impact matrix and market transmission workflow.",
            jurisdiction_focus=["China", "EU"],
            industry_focus=["energy", "manufacturing"],
            created_at=now,
            updated_at=now,
            evidence=[],
        )
    ]


def mock_documents() -> list[Document]:
    now = datetime.now(timezone.utc)
    source = mock_source(
        "source_article_demo",
        "Uploaded market research article",
        "local://storage/documents/demo.md",
    )
    return [
        Document(
            id="doc_demo_001",
            project_id="project_demo_001",
            filename="market-research-demo.md",
            content_type="text/markdown",
            status="parsed_mock",
            parser="markdown_parser",
            uploaded_at=now,
            source=source,
            citations=[],
            evidence=[
                EvidenceItem(
                    id="evidence_doc_demo_001",
                    source_type="uploaded_article",
                    summary="Mock extracted article fact with source trace.",
                    confidence=0.78,
                    source=source,
                )
            ],
        )
    ]


def mock_policies() -> list[Policy]:
    source = mock_source(
        "policy_source_demo_001",
        "Mock policy original page",
        "https://example.gov/policies/mock-policy",
    )
    return [
        Policy(
            id="policy_demo_001",
            title="示例产业政策原文",
            issuer="Mock policy issuer",
            jurisdiction="China",
            policy_type="industrial_policy",
            published_at=datetime(2025, 1, 10, tzinfo=timezone.utc),
            effective_at=datetime(2025, 2, 1, tzinfo=timezone.utc),
            summary="Mock policy record used to shape v0.1 API contracts.",
            source=source,
            sha256="1" * 64,
            citations=[],
            evidence=[
                EvidenceItem(
                    id="policy_demo_001_section_02",
                    source_type="policy_original",
                    summary="Mock cited policy section for impact analysis.",
                    confidence=0.82,
                    source=source,
                )
            ],
        )
    ]
