import jwt
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy import select
from structlog import get_logger

from app.apdapter.uow import CommonRDBUow
from app.application.user.event import UserEventHandler
from app.application.user.model import User
from app.application.user.schema import UserChangePassword, UserCreate, UserLogin, UserResponse, UserUpdate
from app.common.code import Code
from app.common.exception import AuthenticationException401, RequestException400
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
    return CommonRDBUow[User](UserEventHandler, User)


async def create_user(data: UserCreate, operator: Operator) -> UserResponse:
    with get_uow() as uow, uow.transaction():
        user = User.new(data, operator)
        uow.repository.add(user)
        return user.on_created()


async def update_user(user_id: int, data: UserUpdate, operator: Operator) -> UserResponse:
    with get_uow() as uow, uow.transaction():
        user = uow.repository.get(user_id)
        if user is None or user.removed_flag is True:
            raise RequestException400(Code.UNKNOWN_USER)
        user.update(data, operator)
        return user.on_updated()


async def change_password(user_id: int, data: UserChangePassword, operator: Operator) -> None:
    with get_uow() as uow, uow.transaction():
        user = uow.repository.get(user_id)
        if user is None or user.removed_flag is True:
            raise RequestException400(Code.UNKNOWN_USER)
        user.change_password(data, operator)
        user.on_password_updated()


async def remove_user(user_id: int, operator: Operator) -> None:
    with get_uow() as uow, uow.transaction():
        user = uow.repository.get(user_id)
        if user is None or user.removed_flag is True:
            raise RequestException400(Code.UNKNOWN_USER)
        user.remove(operator)
        user.on_removed()


async def login_user(
    data: UserLogin,
) -> Token:
    with get_uow() as uow, uow.transaction():
        user = uow.repository.session.scalar(
            select(User).filter_by(login_id=data.login_id).filter_by(removed_flag=False)
        )
        if user is None:
            raise RequestException400(Code.UNJOINED_ACCOUNT)

        if user.use_flag is False:
            raise RequestException400(Code.UNKNOWN_ADMIN)

        if verify_password(data.password.get_secret_value(), user.password) is False:
            log.warning("password not match")
            raise RequestException400(Code.UNKNOWN_ADMIN)

        uow.repository.add_seen(user)

        user.renew_token()

        return user.on_logged_in()


async def renew_token(refresh_token: str) -> Token:
    with get_uow() as uow, uow.transaction():
        try:
            _scheme, credentials = get_authorization_scheme_param(refresh_token)
            user_id = get_refresh_token_claims(credentials).id
            user = uow.repository.get(user_id)

            if user is None or user.removed_flag is True or user.token is None or not is_validated_jwt(user.token):
                raise AuthenticationException401()

            if user.token and issued_refresh_token_in_10_seconds(user.token):
                return Token(
                    access_token=create_access_token(user),
                    refresh_token=user.token,
                )
            elif user.token == credentials:
                user.renew_token()
                return Token(
                    access_token=create_access_token(user),
                    refresh_token=user.token,
                )
            else:
                raise AuthenticationException401()
        except (jwt.DecodeError, jwt.InvalidTokenError) as e:
            log.exception(e)
            raise AuthenticationException401() from None


async def logout(account_id: int):
    with get_uow() as uow, uow.transaction():
        user = uow.repository.get(account_id)
        if user is None:
            raise RequestException400(Code.UNKNOWN_ADMIN)
        user.sign_out()


async def check_login_id(login_id: str) -> bool:
    with get_uow() as uow:
        return (
            uow.repository.session.scalar(select(User).filter_by(login_id=login_id).filter_by(removed_flag=False))
            is None
        )
