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


def test_core_indexes_are_registered() -> None:
    expected_indexes = {
        "ix_documents_project_id",
        "ix_documents_project_role",
        "ix_document_chunks_document_id",
        "ix_document_chunks_project_id",
        "ix_document_chunks_document_index",
        "ix_policies_jurisdiction",
        "ix_policies_policy_type",
        "ix_policies_publish_date",
        "ix_policies_normalized_title",
        "ix_policies_sha256",
        "ix_policy_versions_policy_id",
        "ix_policy_versions_current",
        "ix_policy_sections_policy_id",
        "ix_policy_sections_version_id",
        "ix_policy_sections_policy_order",
        "ix_claims_project_id",
        "ix_claims_document_id",
        "ix_policy_matches_project_id",
        "ix_policy_matches_claim_id",
        "ix_policy_matches_policy_id",
        "ix_policy_matches_section_id",
        "ix_impact_items_project_id",
        "ix_impact_items_policy_id",
        "ix_analysis_jobs_project_id",
        "ix_analysis_jobs_project_status",
        "ix_analysis_steps_job_id",
        "ix_analysis_steps_job_step",
        "ix_exports_project_id",
        "ix_exports_project_status",
    }
    actual_indexes = {
        index.name
        for table in Base.metadata.tables.values()
        for index in table.indexes
    }

    assert expected_indexes <= actual_indexes


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
