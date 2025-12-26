from abc import ABC
from datetime import UTC, datetime
from typing import Annotated

from pydantic import AwareDatetime, ConfigDict
from pydantic.alias_generators import to_camel
from sqlalchemy import DateTime, TypeDecorator
from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlmodel import Field, SQLModel


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


# SQLModel Base 설정 - 기존 SQLAlchemy Base와 메타데이터 공유
class SQLModelBase(SQLModel):
    """SQLModel 기반 모델을 위한 Base 클래스"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


# SQLModel과 SQLAlchemy가 같은 메타데이터 공유
SQLModelBase.metadata = Base.metadata


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


# SQLModel용 타입 정의
def sa_column_tzdatetime(nullable: bool = False):
    """TZDateTime 컬럼을 위한 SQLModel Field 생성"""
    return Field(sa_type=TZDateTime, nullable=nullable)
