from pydantic import AwareDatetime, Field

from app.application.emoji.schema import EmojiResponse
from app.application.file.schema import FileResponse
from app.application.user.schema import IdCreatedUpdatedDto
from app.common.schema import Schema


class TagBase(Schema):
    user_id: int = Field(..., description="유저 ID")
    name: str = Field(..., description="이름")


class NoticeBase(Schema):
    content: str = Field(..., description="내용")
    tags: list[TagBase] = Field([], description="태그")


class NoticeResponse(IdCreatedUpdatedDto, NoticeBase):
    attachments: list[FileResponse] | None = Field([], description="첨부파일")
    removed_flag: bool = Field(False, description="삭제 여부")
    removed_at: AwareDatetime | None = Field(None, description="삭제 일시")
    removed_reason: str | None = Field(None, description="삭제 사유")
    emojis: list[EmojiResponse] = Field([], description="이모지")
    comment_count: int = Field(0, description="댓글 수")
