from pydantic import AwareDatetime
from sqlalchemy.orm import Mapped, mapped_column, object_session, relationship

from app.apdapter.orm import Base, TZDateTime
from app.application.notice.event import NoticeRemoved
from app.application.notice.schema import NoticeResponse
from app.common.exception import SystemException500
from app.common.model import IdCreatedUpdated
from app.common.type import UserTypeEnum
from app.utils.datetime_utils import utcnow


class Notice(IdCreatedUpdated, Base):
    __tablename__ = "notice"

    title: Mapped[str]
    content: Mapped[str]

    removed_flag: Mapped[bool]
    removed_at: Mapped[AwareDatetime | None] = mapped_column(TZDateTime, nullable=True)

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
        if not session:
            raise SystemException500()
        session.flush()

        event_data = NoticeResponse.model_validate(self)
        self.events.append(NoticeRemoved(data=event_data))
        return event_data
