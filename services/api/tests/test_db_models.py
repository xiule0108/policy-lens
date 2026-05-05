from app.db.base import Base
from app.db.models import Document, LLMProvider, Project


def test_core_tables_are_registered() -> None:
    expected_tables = {
        "projects",
        "documents",
        "document_chunks",
        "policies",
        "policy_versions",
        "policy_sections",
        "claims",
        "policy_matches",
        "impact_items",
        "analysis_jobs",
        "analysis_steps",
        "analysis_results",
        "exports",
        "llm_providers",
        "model_profiles",
    }

    assert expected_tables <= set(Base.metadata.tables)


def test_json_defaults_are_python_containers(db_session) -> None:
    project = Project(name="Energy policy", jurisdictions=["China"], industry="energy")
    provider = LLMProvider(
        provider_key="custom",
        display_name="Custom Provider",
        provider_type="openai_compatible",
    )
    document = Document(
        project=project,
        document_role="research_article",
        file_name="article.md",
        file_type="text/markdown",
    )

    db_session.add_all([project, provider, document])
    db_session.commit()

    assert project.jurisdictions == ["China"]
    assert provider.config == {}
    assert document.metadata_ == {}
