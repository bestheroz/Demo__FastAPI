import jwt
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy import delete, select
from sqlalchemy.sql.functions import count
from structlog import get_logger

from app.application.admin.account.model import AdminAccount
from app.application.admin.account.schema import (
    AdminChangePassword,
    AdminAccountChangeProfile,
    AdminAccountCreate,
    AdminLogin,
    AdminAccountResponse,
    AdminAccountToken,
    AdminAccountVerify,
)
from app.application.admin.account.uow import AdminAccountRDBUow
from app.application.terms.model import Terms
from app.application.user.schema import AccessTokenClaims, RefreshTokenClaims
from app.common.code import Code
from app.common.exception import AuthenticationException401, RequestException400
from app.common.schema import ImageUrlUpdate
from app.utils.jwt import (
    create_access_token,
    create_refresh_token,
    get_refresh_token_claims,
    is_validated_jwt,
    issued_refresh_token_in_10_seconds,
)

log = get_logger()


def remove_temp(email_id: str, uow: AdminAccountRDBUow):
    with uow.autocommit():
        admin_account = uow.admin_account_repo.session.scalar(
            select(AdminAccount)
            .filter_by(login_id=email_id)
            .filter_by(removed_flag=False)
        )

        if admin_account is None:
            raise RequestException400(Code.UNKNOWN_ACCOUNT)

        admin_account.remove()
        [p.remove(1) for p in admin_account.profiles]


def create_admin_account(
    data: AdminAccountCreate,
    uow: AdminAccountRDBUow,
) -> AdminAccountResponse:
    with uow.autocommit():
        admin_account = uow.admin_account_repo.session.scalar(
            select(AdminAccount)
            .filter_by(login_id=data.login_id)
            .filter_by(removed_flag=False)
        )

        if admin_account is not None:
            if admin_account.joined_flag and admin_account.verify_flag:
                raise RequestException400(Code.ALREADY_JOINED_ADMIN_ACCOUNT)
            else:
                # 인증과 가입이 되지 않은 계정이면 삭제 후 새로 생성
                uow.admin_account_repo.session.execute(
                    delete(AdminAccount).filter_by(id=admin_account.id)
                )

        admin_account = AdminAccount.new(data)
        uow.admin_account_repo.add(admin_account)
        return admin_account.on_created()


def verify_admin_account(
    admin_account_id: int,
    data: AdminAccountVerify,
    uow: AdminAccountRDBUow,
) -> AdminAccountToken:
    with uow.autocommit():
        admin_account = uow.admin_account_repo.get(admin_account_id)
        if admin_account is None or admin_account.removed_flag is True:
            raise RequestException400(Code.UNKNOWN_ACCOUNT)

        if admin_account.joined_flag:
            raise RequestException400(Code.ALREADY_JOINED_ADMIN_ACCOUNT)

        if data.verify_token != admin_account.verify_token:
            raise RequestException400(Code.INVALID_VERIFY_TOKEN)

        terms_count = uow.admin_account_repo.session.scalar(
            select(count(Terms.id)).filter_by(service_id=0).filter_by(use_flag=True)
        )
        terms_ids = [t.terms_id for t in data.terms]
        if terms_count != len(terms_ids):
            raise RequestException400(Code.INVALID_TERMS_IDS)

        required_terms = uow.admin_account_repo.session.scalars(
            select(Terms.id)
            .filter_by(service_id=0)
            .filter_by(required_flag=True)
            .filter_by(use_flag=True)
            .filter(Terms.id.in_([t1.terms_id for t1 in data.terms]))
        ).all()
        for terms_id in required_terms:
            if (
                terms_id not in terms_ids
                or next(
                    (t1.agree_flag for t1 in data.terms if t1.terms_id == terms_id),
                    None,
                )
                is False
            ):
                raise RequestException400(Code.REQUIRED_TERMS_NOT_ACCEPTED)
        admin_account.verify(data)
        admin_account.on_joined()
        admin_account.renew_token(_create_refresh_token(admin_account))
        return admin_account.on_logged_in()


def _create_access_token(admin_account: AdminAccount):
    return create_access_token(AccessTokenClaims.model_validate(admin_account))


def _create_refresh_token(admin_account: AdminAccount):
    return create_refresh_token(RefreshTokenClaims.model_validate(admin_account))


def login_admin_account(
    data: AdminLogin,
    uow: AdminAccountRDBUow,
) -> AdminAccountToken:
    with uow.autocommit():
        admin_account = uow.admin_account_repo.session.scalar(
            select(AdminAccount)
            .filter_by(login_id=data.login_id)
            .filter_by(removed_flag=False)
        )
        if admin_account is None:
            raise RequestException400(Code.UNJOINED_ADMIN_ACCOUNT)

        if admin_account.verify_flag is False:
            raise RequestException400(Code.NOT_VERIFIED_ACCOUNT)

        if admin_account.use_flag is False:
            raise RequestException400(Code.UNKNOWN_ACCOUNT)

        if admin_account.check_password(data.password.get_secret_value()) is False:
            log.warning("password not match")
            raise RequestException400(Code.UNKNOWN_ACCOUNT)

        uow.admin_account_repo.add_seen(admin_account)

        admin_account.renew_token(_create_refresh_token(admin_account))

        return admin_account.on_logged_in()


def renew_token(refresh_token: str, uow: AdminAccountRDBUow) -> AdminAccountToken:
    with uow.autocommit():
        try:
            _scheme, credentials = get_authorization_scheme_param(refresh_token)
            admin_account_id = get_refresh_token_claims(credentials).id
            admin_account = uow.admin_account_repo.get(admin_account_id)

            if (
                admin_account is None
                or admin_account.removed_flag is True
                or admin_account.verify_flag is False
                or admin_account.token is None
                or not is_validated_jwt(admin_account.token)
            ):
                raise AuthenticationException401()

            if admin_account.token and issued_refresh_token_in_10_seconds(
                admin_account.token
            ):
                return AdminAccountToken(
                    access_token=_create_access_token(admin_account),
                    refresh_token=admin_account.token,
                )

            elif admin_account.token == credentials:
                refresh_token = _create_refresh_token(admin_account)
                admin_account.renew_token(refresh_token)
                return AdminAccountToken(
                    access_token=_create_access_token(admin_account),
                    refresh_token=refresh_token,
                )
            else:
                raise AuthenticationException401()
        except (jwt.DecodeError, jwt.InvalidTokenError) as e:
            log.exception(e)
            raise AuthenticationException401() from None


def logout(account_id: int, uow: AdminAccountRDBUow):
    with uow.autocommit():
        admin_account = uow.admin_account_repo.get(account_id)
        if admin_account is None:
            raise RequestException400(Code.UNKNOWN_ACCOUNT)
        admin_account.sign_out()


def change_password(
    admin_account_id: int,
    data: AdminChangePassword,
    uow: AdminAccountRDBUow,
) -> AdminAccountResponse:
    with uow.autocommit():
        admin_account = uow.admin_account_repo.get(admin_account_id)
        if admin_account is None:
            raise RequestException400(Code.UNKNOWN_ACCOUNT)

        if admin_account.password and not admin_account.check_password(
            data.password.get_secret_value()
        ):
            log.warning("password not match")
            raise RequestException400(Code.UNKNOWN_ACCOUNT)

        if data.password.get_secret_value() == data.new_password.get_secret_value():
            raise RequestException400(Code.CHANGE_TO_SAME_PASSWORD)

        admin_account.change_password(data.new_password.get_secret_value())
        return admin_account.on_password_changed()


def change_profile(
    admin_account_id: int,
    data: AdminAccountChangeProfile,
    uow: AdminAccountRDBUow,
) -> AdminAccountResponse:
    with uow.autocommit():
        admin_account = uow.admin_account_repo.get(admin_account_id)
        if admin_account is None:
            raise RequestException400(Code.UNKNOWN_ACCOUNT)

        admin_account.change_profile(data)
        return admin_account.on_updated()


def update_admin_account_image_url(
    admin_account_id: int,
    data: ImageUrlUpdate,
    uow: AdminAccountRDBUow,
) -> AdminAccountResponse:
    with uow.autocommit():
        admin_account = uow.admin_account_repo.get(admin_account_id)
        if admin_account is None:
            raise RequestException400(Code.UNKNOWN_ACCOUNT)
        admin_account.update_image_url(data.image_url)
        return admin_account.on_updated()


def remove_admin_account_image_url(
    admin_account_id: int,
    uow: AdminAccountRDBUow,
) -> AdminAccountResponse:
    with uow.autocommit():
        admin_account = uow.admin_account_repo.get(admin_account_id)
        if admin_account is None:
            raise RequestException400(Code.UNKNOWN_ACCOUNT)
        admin_account.update_image_url(None)
        return admin_account.on_updated()


def remove_admin_account(
    admin_account_id: int,
    operator_id: int,
    uow: AdminAccountRDBUow,
) -> None:
    with uow.autocommit():
        admin_account = uow.admin_account_repo.get(admin_account_id)
        if admin_account is None or admin_account.removed_flag is True:
            raise RequestException400(Code.UNKNOWN_ACCOUNT)
        if admin_account.id == operator_id:
            raise RequestException400(Code.CANNOT_REMOVE_YOURSELF)

        admin_account.remove()
        admin_account.on_removed()
