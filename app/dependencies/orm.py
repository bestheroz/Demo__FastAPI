from abc import ABC
from datetime import UTC, datetime
from typing import Annotated

from pydantic import AwareDatetime
from sqlalchemy import DateTime, TypeDecorator
from sqlalchemy.orm import DeclarativeBase, mapped_column


class TZDateTime(TypeDecorator, ABC):
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if value.tzinfo is None:
                raise ValueError("tzinfo is required")
            value = value.astimezone(UTC)
            if isinstance(value, datetime):
                value = datetime(
                    value.year,
                    value.month,
                    value.day,
                    value.hour,
                    value.minute,
                    value.second,
                    value.microsecond,
                    tzinfo=value.tzinfo,
                )
        return value

    def process_result_value(self, value, dialect):
        if not value or value == "0000-00-00 00:00:00":
            return None

        try:
            return value.astimezone(UTC)
        except (ValueError, AttributeError):
            return value.replace(tzinfo=UTC)


class Base(DeclarativeBase):
    __allow_unmapped__ = True


mapped_intpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]
mapped_created_at = Annotated[
    AwareDatetime,
    mapped_column(
        "created_at",
        TZDateTime,
    ),
]
mapped_updated_at = Annotated[
    AwareDatetime,
    mapped_column(
        "updated_at",
        TZDateTime,
    ),
]
