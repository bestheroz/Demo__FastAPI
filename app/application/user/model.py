from pydantic import AwareDatetime
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, object_session, relationship

from app.apdapter.orm import Base, TZDateTime
from app.application.user.event import UserPasswordUpdated, UserRemoved, UserUpdated
from app.application.user.schema import UserCreate, UserResponse, UserUpdate, UserUpdatePassword
from app.common.code import Code
from app.common.exception import RequestException400, SystemException500
from app.common.model import IdCreatedUpdated
from app.common.schema import Operator
from app.common.type import UserTypeEnum
from app.utils.datetime_utils import utcnow
from app.utils.password import get_password_hash, verify_password


class User(IdCreatedUpdated, Base):
    __tablename__ = "user"

    name: Mapped[str]
    use_flag: Mapped[bool]
    login_id: Mapped[str]

    token: Mapped[str | None]
    password: Mapped[str | None]
    change_password_at: Mapped[AwareDatetime | None] = mapped_column(TZDateTime, nullable=True)
    latest_active_at: Mapped[AwareDatetime | None] = mapped_column(TZDateTime, nullable=False)

    joined_at: Mapped[AwareDatetime | None] = mapped_column(TZDateTime, nullable=True)

    additional_info: Mapped[str] = mapped_column(JSON, nullable=False)

    removed_flag: Mapped[bool]
    removed_at: Mapped[AwareDatetime | None] = mapped_column(TZDateTime, nullable=True)

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

    @property
    def type(self):
        return UserTypeEnum.user

    @property
    def created_by(self):
        if self.created_object_type == UserTypeEnum.user:
            return self.created_by_user
        elif self.created_object_type == UserTypeEnum.admin:
            return self.created_by_admin
        raise SystemException500()

    @property
    def updated_by(self):
        if self.updated_object_type == UserTypeEnum.user:
            return self.updated_by_user
        elif self.updated_object_type == UserTypeEnum.admin:
            return self.updated_by_admin
        raise SystemException500()

    @staticmethod
    def new(data: UserCreate, operator: Operator):
        now = utcnow()
        return User(
            name=data.name,
            use_flag=data.use_flag,
            login_id=data.login_id,
            token=None,
            password=get_password_hash(data.password),
            change_password_at=now,
            latest_active_at=now,
            joined_at=now,
            removed_flag=False,
            created_at=now,
            created_by_id=operator.id,
            created_object_type=operator.type,
            updated_at=now,
            updated_by_id=operator.id,
            updated_object_type=operator.type,
        )

    def update(self, data: UserUpdate, operator: Operator):
        now = utcnow()
        self.name = data.name
        self.use_flag = data.use_flag
        self.login_id = data.login_id
        self.updated_at = now
        self.updated_by_id = operator.id
        self.updated_object_type = operator.type
        if data.password:
            self.password = get_password_hash(data.password)
            self.change_password_at = now

    def update_password(self, data: UserUpdatePassword, operator: Operator):
        if verify_password(data.old_password, self.password):
            raise RequestException400(Code.INVALID_PASSWORD)

        now = utcnow()
        self.password = get_password_hash(data.new_password)
        self.change_password_at = now
        self.updated_at = now
        self.updated_by_id = operator.id
        self.updated_object_type = operator.type

    def remove(self, operator: Operator):
        now = utcnow()
        self.removed_flag = True
        self.removed_at = now
        self.updated_at = now
        self.updated_by_id = operator.id
        self.updated_object_type = operator.type

    def on_created(self) -> UserResponse:
        session = object_session(self)
        if not session:
            raise SystemException500()
        session.flush()

        event_data = UserResponse.model_validate(self)
        self.events.append(UserPasswordUpdated(data=event_data))
        return event_data

    def on_updated(self) -> UserResponse:
        session = object_session(self)
        if not session:
            raise SystemException500()
        session.flush()

        event_data = UserResponse.model_validate(self)
        self.events.append(UserUpdated(data=event_data))
        return event_data

    def on_password_updated(self) -> UserResponse:
        session = object_session(self)
        if not session:
            raise SystemException500()
        session.flush()

        event_data = UserResponse.model_validate(self)
        self.events.append(UserPasswordUpdated(data=event_data))
        return event_data

    def on_removed(self) -> UserResponse:
        session = object_session(self)
        if not session:
            raise SystemException500()
        session.flush()

        event_data = UserResponse.model_validate(self)
        self.events.append(UserRemoved(data=event_data))
        return event_data
