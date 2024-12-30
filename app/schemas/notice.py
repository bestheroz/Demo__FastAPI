from pydantic import Field

from app.common.schema import Schema
from app.schemas.user import IdCreatedUpdatedDto


class NoticeBase(Schema):
    title: str = Field(..., description="제목")
    content: str = Field(..., description="내용")
    use_flag: bool = Field(True, description="사용 여부")


class NoticeCreate(NoticeBase):
    pass


class NoticeResponse(IdCreatedUpdatedDto, NoticeBase):
    pass
