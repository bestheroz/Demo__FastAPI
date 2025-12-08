import jwt
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy import select
from sqlalchemy.sql.functions import count
from structlog import get_logger

from app.core.code import Code
from app.core.exception import BadRequestException400, UnauthorizedException401
from app.dependencies.database import transactional
from app.models.user import User
from app.schemas.base import ListResult, Operator, Token
from app.schemas.user import UserChangePassword, UserCreate, UserListRequest, UserLogin, UserResponse, UserUpdate
from app.types.base import UserTypeEnum
from app.utils.jwt import (
    create_access_token,
    get_refresh_token_claims,
    is_validated_jwt,
    issued_refresh_token_in_10_seconds,
)
from app.utils.pagination import get_pagination_list
from app.utils.password import verify_password

log = get_logger()


async def get_users(
    request: UserListRequest,
) -> ListResult[UserResponse]:
    with transactional(readonly=True) as session:
        initial_query = select(User).filter_by(removed_flag=False)
        count_query = select(count(User.id)).filter_by(removed_flag=False)

        if request.id is not None:
            initial_query = initial_query.filter_by(id=request.id)
            count_query = count_query.filter_by(id=request.id)

        if request.login_id is not None:
            initial_query = initial_query.filter(User.login_id.ilike(f"%{request.login_id}%"))
            count_query = count_query.filter(User.login_id.ilike(f"%{request.login_id}%"))

        if request.name is not None:
            initial_query = initial_query.filter(User.name.ilike(f"%{request.name}%"))
            count_query = count_query.filter(User.name.ilike(f"%{request.name}%"))

        if request.use_flag is not None:
            initial_query = initial_query.filter_by(use_flag=request.use_flag)
            count_query = count_query.filter_by(use_flag=request.use_flag)

        return await get_pagination_list(
            session=session,
            initial_query=initial_query,
            count_query=count_query,
            schema_cls=UserResponse,
            page=request.page,
            page_size=request.page_size,
            ordering="-id",
        )


async def get_user(user_id: int) -> UserResponse:
    with transactional(readonly=True) as session:
        result = session.scalar(select(User).filter_by(id=user_id).filter_by(removed_flag=False))
        if result is None:
            raise BadRequestException400(Code.UNKNOWN_USER)
        return UserResponse.model_validate(result)


async def create_user(data: UserCreate, operator: Operator) -> UserResponse:
    with transactional() as session:
        if session.scalar(select(User).filter_by(login_id=data.login_id).filter_by(removed_flag=False)) is not None:
            raise BadRequestException400(Code.ALREADY_JOINED_ACCOUNT)

        user = User.new(data, operator)
        session.add(user)
        return user.on_created()


async def update_user(user_id: int, data: UserUpdate, operator: Operator) -> UserResponse:
    with transactional() as session:
        user = session.scalar(select(User).filter_by(id=user_id))
        if user is None or user.removed_flag:
            raise BadRequestException400(Code.UNKNOWN_USER)

        if (
            session.scalar(
                select(User).filter_by(login_id=data.login_id).filter_by(removed_flag=False).filter(User.id != user_id)
            )
            is not None
        ):
            raise BadRequestException400(Code.ALREADY_JOINED_ACCOUNT)

        user.update(data, operator)
        return user.on_updated()


async def change_password(user_id: int, data: UserChangePassword, operator: Operator) -> UserResponse:
    with transactional() as session:
        user = session.scalar(select(User).filter_by(id=user_id))
        if user is None or user.removed_flag:
            raise BadRequestException400(Code.UNKNOWN_USER)
        if operator.type == UserTypeEnum.USER and user.id != operator.id:
            raise BadRequestException400(Code.CANNOT_CHANGE_OTHERS_PASSWORD)

        if data.old_password.get_secret_value() == data.new_password.get_secret_value():
            raise BadRequestException400(Code.CHANGE_TO_SAME_PASSWORD)

        user.change_password(data, operator)
        return user.on_password_updated()


async def remove_user(user_id: int, operator: Operator) -> None:
    with transactional() as session:
        user = session.scalar(select(User).filter_by(id=user_id))
        if user is None or user.removed_flag:
            raise BadRequestException400(Code.UNKNOWN_USER)
        user.remove(operator)
        user.on_removed()


async def login_user(
    data: UserLogin,
) -> Token:
    with transactional() as session:
        user = session.scalar(select(User).filter_by(login_id=data.login_id).filter_by(removed_flag=False))
        if user is None:
            raise BadRequestException400(Code.UNJOINED_ACCOUNT)

        if not user.use_flag:
            raise BadRequestException400(Code.UNKNOWN_USER)

        if not verify_password(data.password.get_secret_value(), user.password):
            log.warning("User login failed - invalid password", login_id=data.login_id, user_id=user.id)
            raise BadRequestException400(Code.UNKNOWN_USER)

        user.renew_token()

        return user.on_logged_in()


async def renew_token(authorization: str) -> Token:
    with transactional() as session:
        try:
            _scheme, credentials = get_authorization_scheme_param(authorization)
            user_id = get_refresh_token_claims(credentials).id
            user = session.scalar(select(User).filter_by(id=user_id))

            if user is None or user.removed_flag or user.token is None or not is_validated_jwt(user.token):
                raise UnauthorizedException401()

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
                raise UnauthorizedException401()
        except (jwt.DecodeError, jwt.InvalidTokenError) as e:
            log.exception(e)
            raise UnauthorizedException401() from None


async def logout(account_id: int):
    with transactional() as session:
        user = session.scalar(select(User).filter_by(id=account_id))
        if user is None:
            raise BadRequestException400(Code.UNKNOWN_USER)
        user.logout()


async def check_login_id(login_id: str, user_id: int | None) -> bool:
    with transactional(readonly=True) as session:
        query = select(User).filter_by(login_id=login_id).filter_by(removed_flag=False)
        if user_id:
            query = query.filter(User.id != user_id)
        return session.scalar(query) is None
