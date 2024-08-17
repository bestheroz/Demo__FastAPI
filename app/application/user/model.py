from datetime import timedelta
from uuid import uuid4

from pydantic import AwareDatetime, EmailStr
from sqlalchemy import JSON, ForeignKey, String, select
from sqlalchemy.orm import Mapped, mapped_column, object_session, relationship
from sqlalchemy.sql.functions import count

from app.apdapter.orm import Base, TZDateTime
from app.application.user.discipline.model import UserDiscipline
from app.application.user.event import (
    UserPasswordReset,
    UserRecovered,
    UserRemoved,
    UserUpdated,
    UserWithdrew,
)
from app.application.user.history.model import UserHistory
from app.application.user.schema import (
    UserDisciplineResponse,
    UserEvent,
    UserMarketingTermsResponse,
    UserRecovery,
    UserResponse,
)
from app.application.user.terms.model import UserTerms
from app.application.user.type import UserJoinTypeEnum, UserStatusEnum
from app.application.service.type import PlatformEnum
from app.common.type import UserTypeEnum
from app.common.exception import SystemException500
from app.common.model import IdCreatedUpdated
from app.utils.datetime_utils import utcnow


class User(IdCreatedUpdated, Base):
    __tablename__ = "user"

    name: Mapped[str]
    use_flag: Mapped[bool]
    image_url: Mapped[str | None]
    email_id: Mapped[EmailStr] = mapped_column(String, nullable=False)

    login_id: Mapped[str]
    token: Mapped[str | None]
    password: Mapped[bytes | None]
    change_password_at: Mapped[AwareDatetime | None] = mapped_column(
        TZDateTime, nullable=True
    )
    latest_active_at: Mapped[AwareDatetime | None] = mapped_column(
        TZDateTime, nullable=False
    )

    discipline_: Mapped[list["UserDiscipline"]] = relationship(  # type: ignore # noqa: F821
        viewonly=True,
        back_populates="user",
        primaryjoin="User.id == remote(UserDiscipline.user_id)",
    )

    service_id: Mapped[int] = mapped_column(ForeignKey("service.id"))
    service: Mapped["Service"] = relationship(  # type: ignore # noqa: F821
        viewonly=True,
        primaryjoin="foreign(User.service_id) == remote(Service.id)",
    )

    joined_flag: Mapped[bool]
    joined_at: Mapped[AwareDatetime | None] = mapped_column(TZDateTime, nullable=True)
    platform_version: Mapped[str | None]

    terms: Mapped[list[UserTerms]] = relationship(
        lazy="selectin",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    marketing_terms: Mapped[UserMarketingTermsResponse] = mapped_column(
        JSON, nullable=False
    )
    additional_info: Mapped[str] = mapped_column(JSON, nullable=False)

    verify_token: Mapped[str | None]
    verify_flag: Mapped[bool]
    verify_at: Mapped[AwareDatetime | None] = mapped_column(TZDateTime, nullable=True)

    withdraw_flag: Mapped[bool]
    withdraw_at: Mapped[AwareDatetime | None] = mapped_column(TZDateTime, nullable=True)
    withdraw_reason: Mapped[str | None]
    recovery_reason: Mapped[str | None]

    removed_flag: Mapped[bool]
    removed_at: Mapped[AwareDatetime | None] = mapped_column(TZDateTime, nullable=True)

    join_platform: Mapped[PlatformEnum | None]
    join_type: Mapped[UserJoinTypeEnum | None]

    created_by_admin: Mapped["Admin"] = relationship(  # type: ignore # noqa: F821
        viewonly=True,
        primaryjoin="foreign(User.created_by_id) == remote(Admin.id)",
    )
    updated_by_admin: Mapped["Admin"] = relationship(  # type: ignore # noqa: F821
        viewonly=True,
        primaryjoin="foreign(User.updated_by_id) == remote(Admin.id)",
    )

    created_by_user: Mapped["User"] = relationship(
        viewonly=True,
        primaryjoin="foreign(User.created_by_id) == remote(User.id)",
    )
    updated_by_user: Mapped["User"] = relationship(
        viewonly=True,
        primaryjoin="foreign(User.updated_by_id) == remote(User.id)",
    )

    history_description: str | None = None  # 히스토리 용 설명

    @property
    def type(self):
        return UserTypeEnum.user

    @property
    def status(self):
        session = object_session(self)
        if session is None:
            raise SystemException500()
        session.flush()

        user_discipline = session.scalar(
            select(UserDiscipline)
            .filter_by(user_id=self.id)
            .filter(UserDiscipline.release_flag.is_(False))
            .filter(UserDiscipline.start_at <= utcnow())
            .filter(UserDiscipline.end_at >= utcnow())
        )
        if user_discipline is not None:
            return UserStatusEnum.DISCIPLINED
        # TODO joony: 징계 상태도 구현
        return UserStatusEnum.ACTIVE

    @property
    def history(self):
        session = object_session(self)
        if session is None:
            raise SystemException500()
        session.flush()

        return session.scalars(
            select(UserHistory)
            .filter_by(user_id=self.id)
            .order_by(UserHistory.id.desc())
            .limit(3)
        ).all()

    @property
    def discipline(self):
        session = object_session(self)
        if session is None:
            raise SystemException500()
        session.flush()

        count_user_discipline = session.scalar(
            select(count(UserDiscipline.id))
            .filter_by(user_id=self.id)
            .filter(UserDiscipline.release_flag.is_(False))
        )
        user_discipline = session.scalar(
            select(UserDiscipline)
            .filter_by(user_id=self.id)
            .filter(UserDiscipline.release_flag.is_(False))
            .filter(UserDiscipline.start_at <= utcnow())
            .filter(UserDiscipline.end_at >= utcnow())
        )

        return (
            UserDisciplineResponse.model_validate(user_discipline).dict()
            if user_discipline is not None
            else {}
            | {
                "discipline_flag": True,
                "discipline_cnt": count_user_discipline,
            }
        )

    @property
    def report(self):
        # TODO joony
        return {
            "total_report_count": 0,
            "reported_board_cnt": 0,
            "reported_cnt": 0,
        }

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

    @property
    def archive_expiration_at(self):
        return self.withdraw_at + timedelta(days=365) if self.withdraw_at else None

    def reset_password(self, operator_id: int):
        now = utcnow()
        self.password = None
        self.verify_token = uuid4().hex
        self.updated_at = now
        self.updated_by_id = operator_id
        self.updated_object_type = UserTypeEnum.admin
        self.history_description = "비밀번호 초기화"

    def update_image_url(self, image_url: str | None, operator_id: int):
        self.image_url = image_url
        self.updated_at = utcnow()
        self.updated_by_id = operator_id
        self.updated_object_type = UserTypeEnum.admin
        self.history_description = (
            "프로필 이미지 변경" if image_url else "프로필 이미지 초기화"
        )

    def withdraw(self, operator_id: int):
        now = utcnow()
        self.withdraw_flag = True
        self.withdraw_at = now
        self.updated_at = now
        self.updated_by_id = operator_id
        self.updated_object_type = UserTypeEnum.admin
        self.history_description = "유저 탈퇴"

    def remove(self, operator_id: int):
        now = utcnow()
        self.removed_flag = True
        self.removed_at = now
        self.updated_at = now
        self.updated_by_id = operator_id
        self.updated_object_type = UserTypeEnum.admin
        self.history_description = "유저 삭제"

    def recovery(self, data: UserRecovery, operator_id: int):
        now = utcnow()
        self.withdraw_flag = False
        self.withdraw_at = None
        self.recovery_reason = data.reason
        self.updated_at = now
        self.updated_by_id = operator_id
        self.updated_object_type = UserTypeEnum.admin
        self.history_description = "유저 탈퇴 복구"

    def on_password_reset(self) -> UserResponse:
        session = object_session(self)
        if session is None:
            raise SystemException500()
        session.flush()
        self.events.append(UserPasswordReset(data=UserEvent.model_validate(self)))
        return UserResponse.model_validate(self)

    def on_withdraw(self) -> UserResponse:
        session = object_session(self)
        if session is None:
            raise SystemException500()
        session.flush()
        event_data = UserResponse.model_validate(self)
        self.events.append(UserWithdrew(data=event_data))
        return event_data

    def on_removed(self) -> UserResponse:
        session = object_session(self)
        if session is None:
            raise SystemException500()
        session.flush()
        event_data = UserResponse.model_validate(self)
        self.events.append(UserRemoved(data=event_data))
        return event_data

    def on_recovery(self) -> UserResponse:
        session = object_session(self)
        if session is None:
            raise SystemException500()
        session.flush()
        event_data = UserResponse.model_validate(self)
        self.events.append(UserRecovered(data=event_data))
        return event_data

    def on_updated(self) -> UserResponse:
        session = object_session(self)
        if session is None:
            raise SystemException500()
        session.flush()
        event_data = UserResponse.model_validate(self)
        self.events.append(UserUpdated(data=event_data))
        return event_data
