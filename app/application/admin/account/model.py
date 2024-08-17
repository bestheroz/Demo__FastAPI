from uuid import uuid4

from pydantic import AwareDatetime
from sqlalchemy import JSON, desc
from sqlalchemy.orm import Mapped, mapped_column, object_session, relationship

from app.apdapter.orm import (
    Base,
    TZDateTime,
    mapped_created_at,
    mapped_intpk,
    mapped_updated_at,
)
from app.application.admin.account.event import (
    AdminCreated,
    AdminAccountDeleted,
    AdminAccountJoined,
    AdminAccountLoggedIn,
    AdminAccountPasswordChanged,
    AdminAccountUpdated,
)
from app.application.admin.account.schema import (
    AdminAccountChangeProfile,
    AdminAccountCreate,
    AdminAccountCreateEvent,
    AdminAccountMarketingTermsCreate,
    AdminAccountResponse,
    AdminAccountToken,
    AdminAccountUpdate,
    AdminAccountVerify,
)
from app.application.admin.account.terms.model import AdminAccountTerms
from app.application.admin.schema import AdminInvite
from app.application.user.schema import UserMarketingTermsResponse
from app.application.user.schema import AccessTokenClaims, ServiceAuthority
from app.common.type import UserTypeEnum
from app.common.exception import SystemException500
from app.utils.datetime_utils import utcnow
from app.utils.jwt import create_access_token
from app.utils.password import hash_password, match_password


class AdminAccount(Base):
    __tablename__ = "admin_account"

    id: Mapped[mapped_intpk]
    login_id: Mapped[str]  # email_id
    name: Mapped[str]
    use_flag: Mapped[bool]
    manager_flag: Mapped[bool]
    image_url: Mapped[str | None]

    profiles: Mapped[list["Admin"]] = relationship(  # type: ignore # noqa: F821
        lazy="selectin",
        back_populates="account",
        primaryjoin="and_(AdminAccount.id == remote(Admin.account_id), "
        "Admin.removed_flag.is_(False), Admin.use_flag.is_(True))",
        order_by=desc("id"),
    )
    terms: Mapped[list["AdminAccountTerms"]] = relationship(
        lazy="selectin",
        primaryjoin="AdminAccount.id == remote(AdminAccountTerms.account_id)",
        cascade="all, delete-orphan",
    )
    marketing_terms: Mapped[UserMarketingTermsResponse] = mapped_column(
        JSON, nullable=False
    )

    token: Mapped[str | None]
    password: Mapped[str | None]
    change_password_at: Mapped[AwareDatetime | None] = mapped_column(
        TZDateTime, nullable=True
    )
    latest_active_at: Mapped[AwareDatetime | None] = mapped_column(
        TZDateTime, nullable=False
    )

    joined_flag: Mapped[bool]
    joined_at: Mapped[AwareDatetime | None] = mapped_column(TZDateTime, nullable=True)

    verify_token: Mapped[str | None]
    verify_flag: Mapped[bool]
    verify_at: Mapped[AwareDatetime | None] = mapped_column(TZDateTime, nullable=True)

    removed_flag: Mapped[bool]
    removed_at: Mapped[AwareDatetime | None] = mapped_column(TZDateTime, nullable=True)

    created_at: Mapped[mapped_created_at]
    updated_at: Mapped[mapped_updated_at]

    @property
    def service_authorities(self) -> list[ServiceAuthority]:
        # 매니저일 경우 모든 권한을 가지고 있으므로 토큰 길이를 줄이기 위해 빈 리스트를 리턴한다.
        if self.manager_flag is True:
            return []

        if self.profiles is None:
            return []

        return [
            ServiceAuthority(
                id=p.id,
                service_id=p.service_id,
                manager_flag=p.manager_flag,
                authorities=p.authorities,
            )
            for p in self.profiles
        ]

    @property
    def email_id(self):
        return self.login_id

    @property
    def type(self):
        return UserTypeEnum.admin_account

    @staticmethod
    def new(data: AdminInvite | AdminAccountCreate) -> "AdminAccount":
        now = utcnow()
        return AdminAccount(
            **data.model_dump(exclude={"id", "email_id"}),
            name=data.login_id,
            use_flag=False,
            manager_flag=False,
            marketing_terms=AdminAccountMarketingTermsCreate(
                email_agree_flag=False,
                sms_agree_flag=False,
                call_agree_flag=False,
                post_agree_flag=False,
            ).model_dump(),  # type: ignore
            removed_flag=False,
            verify_flag=False,
            verify_token=uuid4().hex,
            joined_flag=False,
            created_at=now,
            updated_at=now,
        )

    def verify(self, data: AdminAccountVerify):
        now = utcnow()
        self.terms = [AdminAccountTerms.new(t, 1) for t in data.terms]
        self.name = data.name
        self.password = hash_password(data.password.get_secret_value())
        self.use_flag = True
        self.marketing_terms = data.marketing_terms.to_response().model_dump()  # type: ignore
        self.verify_flag = True
        self.verify_at = now
        self.joined_flag = True
        self.joined_at = now
        self.change_password_at = now
        self.updated_at = now

    def update(self, data: AdminAccountUpdate):
        # self.terms 에서 삭제된 항목을 제거
        self.terms = [t for t in self.terms if t.id in [t.id for t in data.terms]]

        for t in data.terms:
            if t.id is None:
                self.terms.append(AdminAccountTerms.new(t, 1))
            else:
                [mt.update(t, 1) for mt in self.terms if mt.id == t.id]

        self.name = data.name  # type: ignore
        self.login_id = data.login_id
        self.use_flag = data.use_flag
        self.marketing_terms = data.marketing_terms.to_response().model_dump()  # type: ignore
        self.image_url = data.image_url
        self.updated_at = utcnow()

    def update_image_url(self, image_url: str | None):
        self.image_url = image_url
        self.updated_at = utcnow()

    def remove(self):
        now = utcnow()
        self.removed_flag = True
        self.removed_at = now
        self.updated_at = now

    def renew_token(self, refresh_token: str):
        self.token = refresh_token
        self.latest_active_at = utcnow()

    def sign_out(self):
        self.token = None

    def check_password(self, password: str):
        return match_password(self.password, password)

    def change_password(self, password: str):
        now = utcnow()
        self.password = hash_password(password)
        self.change_password_at = now
        self.updated_at = now

    def change_profile(self, data: AdminAccountChangeProfile):
        now = utcnow()
        self.name = data.name
        self.updated_at = now

    def on_created(self) -> AdminAccountResponse:
        session = object_session(self)
        if session is None:
            raise SystemException500()
        session.flush()
        self.events.append(
            AdminCreated(data=(AdminAccountCreateEvent.model_validate(self)))
        )
        return AdminAccountResponse.model_validate(self)

    def on_updated(self) -> AdminAccountResponse:
        session = object_session(self)
        if session is None:
            raise SystemException500()
        session.flush()
        event_data = AdminAccountResponse.model_validate(self)
        self.events.append(AdminAccountUpdated(data=event_data))
        return event_data

    def on_removed(self) -> AdminAccountResponse:
        session = object_session(self)
        if session is None:
            raise SystemException500()
        session.flush()
        event_data = AdminAccountResponse.model_validate(self)
        self.events.append(AdminAccountDeleted(data=event_data))
        return event_data

    def on_joined(self) -> AdminAccountResponse:
        session = object_session(self)
        if session is None:
            raise SystemException500()
        session.flush()
        event_data = AdminAccountResponse.model_validate(self)
        self.events.append(AdminAccountJoined(data=event_data))
        return event_data

    def on_logged_in(self) -> AdminAccountToken:
        session = object_session(self)
        if session is None:
            raise SystemException500()
        session.flush()
        self.events.append(
            AdminAccountLoggedIn(data=(AdminAccountResponse.model_validate(self)))
        )
        if self.token is None:
            raise SystemException500()
        return AdminAccountToken(
            access_token=create_access_token(AccessTokenClaims.model_validate(self)),
            refresh_token=self.token,
        )

    def on_password_changed(self) -> AdminAccountResponse:
        session = object_session(self)
        if session is None:
            raise SystemException500()
        session.flush()
        event_data = AdminAccountResponse.model_validate(self)
        self.events.append(AdminAccountPasswordChanged(data=event_data))
        return event_data
