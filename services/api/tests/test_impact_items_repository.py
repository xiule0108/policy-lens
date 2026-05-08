from uuid import uuid4

from app.repositories.impact_items import (
    create_impact_items,
    delete_impact_items_for_analysis,
    get_impact_item,
    list_impact_items,
)
from app.repositories.policies import create_policy
from app.repositories.projects import create_project


def test_impact_items_repository_filters_and_deletes(db_session) -> None:
    project = create_project(db_session, {"name": "Impact item project"})
    policy = create_policy(db_session, {"title": "Energy impact policy"})
    analysis_id = uuid4()

    items = create_impact_items(
        db_session,
        [
            {
                "project_id": project.id,
                "analysis_id": analysis_id,
                "policy_id": policy.id,
                "impact_subject": "investor",
                "impact_direction": "positive",
                "impact_horizon": "medium",
                "impact_mechanism": "price_mechanism",
                "market_variable": "electricity_price",
                "analysis_text": "rule_based_assessment: price impact.",
                "confidence": 0.7,
                "citations": [
                    {"source_type": "claim", "claim_id": "claim-1"},
                    {"source_type": "policy_section", "policy_section_id": "section-1"},
                ],
            }
        ],
    )

    assert get_impact_item(db_session, items[0].id).id == items[0].id
    assert list_impact_items(db_session, analysis_id=analysis_id)[0].id == items[0].id
    assert list_impact_items(db_session, policy_id=policy.id)[0].id == items[0].id
    assert list_impact_items(db_session, impact_direction="positive")[0].id == items[0].id
    assert list_impact_items(db_session, impact_subject="investor")[0].id == items[0].id
    assert list_impact_items(db_session, project_id=project.id)[0].citations[0]["source_type"] == "claim"

    delete_impact_items_for_analysis(db_session, analysis_id)

    assert list_impact_items(db_session, analysis_id=analysis_id) == []
