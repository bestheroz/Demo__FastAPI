import jwt
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy import select
from structlog import get_logger

from app.apdapter.uow import CommonRDBUow
from app.application.admin.event import AdminEventHandler
from app.application.admin.model import Admin
from app.application.admin.schema import (
    AdminChangePassword,
    AdminCreate,
    AdminLogin,
    AdminResponse,
    AdminUpdate,
)
from app.common.code import Code
from app.common.exception import BadRequestException400, UnauthorizedException401
from app.common.schema import Operator, Token
from app.utils.jwt import (
    create_access_token,
    get_refresh_token_claims,
    is_validated_jwt,
    issued_refresh_token_in_10_seconds,
)
from app.utils.password import verify_password

log = get_logger()


def get_uow():
    return CommonRDBUow[Admin](AdminEventHandler, Admin)


async def create_admin(
    data: AdminCreate,
    operator_id: int,
) -> AdminResponse:
    with get_uow() as uow, uow.transaction():
        if (
            uow.repository.session.scalar(select(Admin).filter_by(login_id=data.login_id).filter_by(removed_flag=False))
            is not None
        ):
            raise BadRequestException400(Code.ALREADY_JOINED_ACCOUNT)

        admin = Admin.new(data, operator_id)
        uow.repository.add(admin)
        return admin.on_created()


async def update_admin(
    admin_id: int,
    data: AdminUpdate,
    operator: Operator,
) -> AdminResponse:
    with get_uow() as uow, uow.transaction():
        admin = uow.repository.get(admin_id)
        if admin is None or admin.removed_flag is True:
            raise BadRequestException400(Code.UNKNOWN_USER)
        if admin.manager_flag is False and admin.id == operator.id:
            raise BadRequestException400(Code.CANNOT_UPDATE_YOURSELF)
        if admin.manager_flag != data.manager_flag and operator.manager_flag is False:
            raise BadRequestException400(Code.UNKNOWN_AUTHORITY)
        if (
            uow.repository.session.scalar(
                select(Admin)
                .filter_by(login_id=data.login_id)
                .filter_by(removed_flag=False)
                .filter(Admin.id != admin_id)
            )
            is not None
        ):
            raise BadRequestException400(Code.ALREADY_JOINED_ACCOUNT)

        admin.update(data, operator.id)
        return admin.on_updated()


async def remove_admin(
    admin_id: int,
    operator_id: int,
) -> None:
    with get_uow() as uow, uow.transaction():
        admin = uow.repository.get(admin_id)
        if admin is None:
            raise BadRequestException400(Code.UNKNOWN_USER)
        if admin.id == operator_id:
            raise BadRequestException400(Code.CANNOT_REMOVE_YOURSELF)
        admin.remove(operator_id)
        admin.on_removed()


async def change_password(
    admin_id: int,
    data: AdminChangePassword,
    operator: Operator,
) -> AdminResponse:
    with get_uow() as uow, uow.transaction():
        admin = uow.repository.get(admin_id)
        if admin is None or admin.removed_flag is True:
            raise BadRequestException400(Code.UNKNOWN_ADMIN)

        if admin.password and not verify_password(data.old_password.get_secret_value(), admin.password):
            log.warning("password not match")
            raise BadRequestException400(Code.UNKNOWN_ADMIN)

        if data.old_password.get_secret_value() == data.new_password.get_secret_value():
            raise BadRequestException400(Code.CHANGE_TO_SAME_PASSWORD)

        admin.change_password(data.new_password.get_secret_value(), operator)
        return admin.on_password_changed()


async def login_admin(
    data: AdminLogin,
) -> Token:
    with get_uow() as uow, uow.transaction():
        admin = uow.repository.session.scalar(
            select(Admin).filter_by(login_id=data.login_id).filter_by(removed_flag=False)
        )
        if admin is None:
            raise BadRequestException400(Code.UNJOINED_ACCOUNT)

        if admin.use_flag is False:
            raise BadRequestException400(Code.UNKNOWN_ADMIN)

        if verify_password(data.password.get_secret_value(), admin.password) is False:
            log.warning("password not match")
            raise BadRequestException400(Code.UNKNOWN_ADMIN)

        admin.renew_token()

        return admin.on_logged_in()


async def renew_token(refresh_token: str) -> Token:
    with get_uow() as uow, uow.transaction():
        try:
            _scheme, credentials = get_authorization_scheme_param(refresh_token)
            admin_id = get_refresh_token_claims(credentials).id
            admin = uow.repository.get(admin_id)

            if admin is None or admin.removed_flag is True or admin.token is None or not is_validated_jwt(admin.token):
                raise UnauthorizedException401()

            if admin.token and issued_refresh_token_in_10_seconds(admin.token):
                return Token(
                    access_token=create_access_token(admin),
                    refresh_token=admin.token,
                )
            elif admin.token == credentials:
                admin.renew_token()
                return Token(
                    access_token=create_access_token(admin),
                    refresh_token=admin.token,
                )
            else:
                raise UnauthorizedException401()
        except (jwt.DecodeError, jwt.InvalidTokenError) as e:
            log.exception(e)
            raise UnauthorizedException401() from None


async def logout(account_id: int):
    with get_uow() as uow, uow.transaction():
        admin = uow.repository.get(account_id)
        if admin is None:
            raise BadRequestException400(Code.UNKNOWN_ADMIN)
        admin.logout()


async def check_login_id(login_id: str, admin_id: int | None) -> bool:
    with get_uow() as uow:
        query = select(Admin).filter_by(login_id=login_id).filter_by(removed_flag=False)
        if admin_id:
            query = query.filter(Admin.id != admin_id)
        return uow.repository.session.scalar(query) is None
