from pydantic import AwareDatetime
from sqlalchemy import or_, select
from sqlalchemy.sql.functions import count

from app.apdapter.orm import session_scope
from app.application.user.model import User
from app.application.user.schema import (
    UserResponse,
)
from app.common.code import Code
from app.common.exception import RequestException400
from app.common.schema import ListApiResult
from app.utils.pagination import get_pagination_list


def get_users(
    page: int,
    page_size: int,
    ordering: str | None = None,
    search: str | None = None,
    ids: set[int] | None = None,
    joined_start_at: AwareDatetime | None = None,
    joined_end_at: AwareDatetime | None = None,
) -> ListApiResult[UserResponse]:
    initial_query = (
        select(User)
        .filter_by(removed_flag=False)
        .filter_by(withdraw_flag=False)
        .filter_by(verify_flag=True)
    )
    count_query = (
        select(count(User.id))
        .filter_by(removed_flag=False)
        .filter_by(withdraw_flag=False)
        .filter_by(verify_flag=True)
    )

    if search:
        initial_query = initial_query.filter(
            or_(User.name.ilike(f"%{search}%"), User.login_id.ilike(f"%{search}%"))
        )
        count_query = count_query.filter(
            or_(User.name.ilike(f"%{search}%"), User.login_id.ilike(f"%{search}%"))
        )

    if ids:
        initial_query = initial_query.filter(User.id.in_(ids))
        count_query = count_query.filter(User.id.in_(ids))

    if joined_start_at:
        initial_query = initial_query.filter(User.joined_at >= joined_start_at)
        count_query = count_query.filter(User.joined_at >= joined_start_at)

    if joined_end_at:
        initial_query = initial_query.filter(User.joined_at <= joined_end_at)
        count_query = count_query.filter(User.joined_at <= joined_end_at)

    return get_pagination_list(
        initial_query=initial_query,
        count_query=count_query,
        schema_cls=UserResponse,
        page=page,
        page_size=page_size,
        ordering=ordering,
    )


def get_user(user_id: int) -> UserResponse:
    with session_scope() as session:
        result = session.scalar(
            select(User).filter_by(id=user_id).filter_by(removed_flag=False)
        )
        if result is None:
            raise RequestException400(Code.UNKNOWN_USER)
        return UserResponse.model_validate(result)
