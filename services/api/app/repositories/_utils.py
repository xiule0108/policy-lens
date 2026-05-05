from __future__ import annotations

import uuid


def coerce_uuid(value) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


def coerce_optional_uuid(value) -> uuid.UUID | None:
    if value in (None, ""):
        return None
    return coerce_uuid(value)
