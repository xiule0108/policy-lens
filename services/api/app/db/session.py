"""Database session placeholder.

v0.1 keeps API routes mock-only. PostgreSQL wiring will be added once the
project, document, policy, and evidence schemas are finalized.
"""


def get_database_status() -> dict[str, str]:
    return {"status": "not_connected", "mode": "v0.1_mock"}
