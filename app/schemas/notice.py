"""
Notice 스키마 - SQLModel 기반 모델에서 re-export

스키마 정의는 app/models/notice.py로 통합되었습니다.
하위 호환성을 위해 기존 import 경로를 유지합니다.
"""

from pydantic import Field

from app.models.notice import NoticeBase, NoticeCreate, NoticeResponse
from app.schemas.base import Pagination

# Re-export for backward compatibility
__all__ = ["NoticeBase", "NoticeCreate", "NoticeResponse", "NoticeListRequest"]


class NoticeListRequest(Pagination):
    id: int | None = Field(None, description="ID(KEY)")
    title: str | None = Field(None, description="제목")
    use_flag: bool | None = Field(None, description="사용 여부")
