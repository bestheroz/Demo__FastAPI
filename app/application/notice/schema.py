from pydantic import Field

from app.application.user.schema import IdCreatedUpdatedDto
from app.common.schema import Schema


class NoticeBase(Schema):
    title: str = Field(..., description="제목")
    content: str = Field(..., description="내용")


class NoticeCreate(NoticeBase):
    pass


class NoticeResponse(IdCreatedUpdatedDto, NoticeBase):
    pass
