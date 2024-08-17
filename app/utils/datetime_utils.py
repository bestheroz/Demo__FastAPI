from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from pydantic import AwareDatetime


def utcnow() -> AwareDatetime:
    return datetime.now(UTC)


def now_iso8601_string():
    return utcnow().isoformat().replace("+00:00", "Z")


def to_iso8601_string(dt: AwareDatetime | datetime | None):
    return dt.isoformat().replace("+00:00", "Z") if dt else "-"


def format_to_kst_tz(dt: AwareDatetime | datetime | None, pattern: str):
    return dt.astimezone(ZoneInfo("Asia/Seoul")).strftime(pattern) if dt else "-"
