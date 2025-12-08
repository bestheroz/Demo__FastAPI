from datetime import UTC, datetime

from pydantic import AwareDatetime


def utcnow() -> AwareDatetime:
    return datetime.now(UTC)
