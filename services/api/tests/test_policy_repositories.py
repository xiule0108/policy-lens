from datetime import date

from app.repositories.policies import create_policy, list_policies, search_policies_by_keyword, update_policy
from app.repositories.policy_sections import count_policy_sections, create_policy_sections, list_policy_sections
from app.repositories.policy_versions import (
    create_policy_version,
    get_current_policy_version,
    list_policy_versions,
    set_policy_versions_not_current,
)


def test_policy_repository_filters_and_updates(db_session) -> None:
    first = create_policy(
        db_session,
        {
            "title": "新能源汽车消纳管理办法",
            "normalized_title": "新能源汽车消纳管理办法",
            "issuer": "国家能源局",
            "jurisdiction": "China",
            "policy_type": "notice",
            "publish_date": date(2026, 1, 2),
            "status": "active",
        },
    )
    create_policy(
        db_session,
        {
            "title": "European market memo",
            "issuer": "EU Commission",
            "jurisdiction": "EU",
            "policy_type": "memo",
            "status": "draft",
        },
    )

    assert [policy.id for policy in list_policies(db_session, query="新能源")] == [first.id]
    assert [policy.id for policy in list_policies(db_session, jurisdiction="China")] == [first.id]
    assert [policy.id for policy in list_policies(db_session, issuer="能源")] == [first.id]
    assert [policy.id for policy in list_policies(db_session, policy_type="notice")] == [first.id]
    assert [policy.id for policy in list_policies(db_session, status="active")] == [first.id]
    assert [policy.id for policy in search_policies_by_keyword(db_session, "消纳")] == [first.id]

    updated = update_policy(db_session, first.id, {"status": "superseded", "issuer_level": "national"})

    assert updated is not None
    assert updated.status == "superseded"
    assert updated.issuer_level == "national"


def test_policy_versions_and_sections_repository(db_session) -> None:
    policy = create_policy(db_session, {"title": "Policy with versions"})
    first_version = create_policy_version(
        db_session,
        {
            "policy_id": policy.id,
            "version_label": "v1",
            "normalized_text": "first text",
            "sha256": "a" * 64,
            "is_current": True,
        },
    )
    set_policy_versions_not_current(db_session, policy.id)
    second_version = create_policy_version(
        db_session,
        {
            "policy_id": policy.id,
            "version_label": "v2",
            "normalized_text": "second text",
            "sha256": "b" * 64,
            "is_current": True,
        },
    )

    assert get_current_policy_version(db_session, policy.id).id == second_version.id
    assert [version.id for version in list_policy_versions(db_session, policy.id)] == [
        second_version.id,
        first_version.id,
    ]

    sections = create_policy_sections(
        db_session,
        [
            {
                "policy_id": policy.id,
                "version_id": second_version.id,
                "section_path": "General",
                "heading": "General",
                "content": "First section",
                "order_index": 0,
                "token_count": 10,
                "metadata": {"source_chunk_index": 0},
            },
            {
                "policy_id": policy.id,
                "version_id": second_version.id,
                "content": "Second section",
                "order_index": 1,
                "token_count": 12,
            },
        ],
    )

    assert len(sections) == 2
    assert count_policy_sections(db_session, policy.id, version_id=second_version.id) == 2
    assert [section.content for section in list_policy_sections(db_session, policy.id)] == [
        "First section",
        "Second section",
    ]
