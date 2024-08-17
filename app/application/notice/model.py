from pydantic import AwareDatetime
from sqlalchemy import JSON, ForeignKey, select
from sqlalchemy.orm import Mapped, mapped_column, object_session, relationship
from sqlalchemy.sql.functions import count

from app.apdapter.orm import Base, TZDateTime
from app.application.comment.model import Comment
from app.application.comment.type import CommentObjectTypeEnum
from app.application.emoji.model import Emoji
from app.application.emoji.types import EmojiObjectTypeEnum
from app.application.file.model import File
from app.application.file.type import FileObjectTypeEnum
from app.application.notice.event import NoticeRemoved
from app.application.notice.schema import NoticeResponse, TagBase
from app.application.notice.type import NoticeStatusEnum
from app.common.type import UserTypeEnum
from app.common.exception import SystemException500
from app.common.model import IdCreatedUpdated
from app.utils.datetime_utils import utcnow


class Notice(IdCreatedUpdated, Base):
    __tablename__ = "notice"

    content: Mapped[str]

    tags: Mapped[list[TagBase]] = mapped_column(JSON, nullable=False)
    emojis: Mapped[list[Emoji]] = relationship(
        lazy="selectin",
        primaryjoin="and_(foreign(Notice.id) == remote(Emoji.object_id), "
        f"remote(Emoji.object_type) == '{EmojiObjectTypeEnum.notice}')",
        uselist=True,
        single_parent=True,
        viewonly=True,
    )
    attachments: Mapped[list[File] | None] = relationship(
        lazy="selectin",
        primaryjoin="and_(foreign(Notice.id) == remote(File.object_id), "
        f"remote(File.object_type) == '{FileObjectTypeEnum.notice}')",
        uselist=True,
        cascade="all, delete-orphan",
        single_parent=True,
    )

    service_id: Mapped[int] = mapped_column(ForeignKey("service.id"))

    removed_flag: Mapped[bool]
    removed_at: Mapped[AwareDatetime | None] = mapped_column(TZDateTime, nullable=True)
    removed_reason: Mapped[str | None]

    created_by_admin: Mapped["Admin"] = relationship(  # type: ignore # noqa: F821
        viewonly=True,
        primaryjoin="foreign(Notice.created_by_id) == remote(Admin.id)",
    )
    updated_by_admin: Mapped["Admin"] = relationship(  # type: ignore # noqa: F821
        viewonly=True,
        primaryjoin="foreign(Notice.updated_by_id) == remote(Admin.id)",
    )

    created_by_user: Mapped["User"] = relationship(  # type: ignore # noqa: F821
        viewonly=True,
        primaryjoin="foreign(Notice.created_by_id) == remote(User.id)",
    )
    updated_by_user: Mapped["User"] = relationship(  # type: ignore # noqa: F821
        viewonly=True,
        primaryjoin="foreign(Notice.updated_by_id) == remote(User.id)",
    )

    @property
    def status(self):
        if self.removed_flag is True:
            return (
                NoticeStatusEnum.REMOVED_BY_ADMIN
                if self.updated_object_type == UserTypeEnum.admin
                else NoticeStatusEnum.REMOVED_BY_MEMBER
            )
        return NoticeStatusEnum.ACTIVE

    @property
    def comment_count(self) -> int:
        session = object_session(self)
        if session is None:
            raise SystemException500()
        return (
            session.scalar(
                select(count(Comment.id))
                .filter_by(object_id=self.id)
                .filter_by(object_type=CommentObjectTypeEnum.notice)
                .filter_by(removed_flag=False)
            )
            or 0
        )

    @property
    def created_by(self):
        if self.created_object_type == UserTypeEnum.user.lower():
            return self.created_by_user
        elif self.created_object_type == UserTypeEnum.admin:
            return self.created_by_admin
        raise SystemException500()

    @property
    def updated_by(self):
        if self.updated_object_type == UserTypeEnum.user.lower():
            return self.updated_by_user
        elif self.updated_object_type == UserTypeEnum.admin:
            return self.updated_by_admin
        raise SystemException500()

    def remove(self, operator_id: int):
        now = utcnow()
        self.removed_flag = True
        self.removed_at = now
        self.updated_at = now
        self.updated_by_id = operator_id
        self.updated_object_type = UserTypeEnum.admin

    def on_removed(self) -> NoticeResponse:
        session = object_session(self)
        if session is None:
            raise SystemException500()
        session.flush()
        event_data = NoticeResponse.model_validate(self)
        self.events.append(NoticeRemoved(data=event_data))
        return event_data
