from pydantic import AwareDatetime
from sqlalchemy import and_, literal, not_, or_, select
from sqlalchemy.orm import noload
from sqlalchemy.sql.functions import count

from app.apdapter.orm import session_scope
from app.application.user.discipline.model import UserDiscipline
from app.application.user.model import User
from app.application.user.schema import (
    UserDetailResponse,
    UserResponse,
    UserSimple,
)
from app.application.user.type import UserJoinTypeEnum, UserStatusEnum
from app.common.code import Code
from app.common.exception import RequestException400
from app.common.schema import ListApiResult
from app.utils.datetime_utils import utcnow
from app.utils.pagination import get_pagination_list


def get_users_by_service_id(
    service_id: int,
    page: int,
    page_size: int,
    ordering: str | None = None,
    search: str | None = None,
    ids: set[int] | None = None,
    join_types: set[UserJoinTypeEnum] | None = None,
    joined_start_at: AwareDatetime | None = None,
    joined_end_at: AwareDatetime | None = None,
    status: set[UserStatusEnum] | None = None,
    report_counts: set[int] | None = None,
) -> ListApiResult[UserResponse]:
    initial_query = (
        select(User)
        .filter_by(service_id=service_id)
        .filter_by(removed_flag=False)
        .filter_by(withdraw_flag=False)
        .filter_by(verify_flag=True)
    )
    count_query = (
        select(count(User.id))
        .filter_by(service_id=service_id)
        .filter_by(removed_flag=False)
        .filter_by(withdraw_flag=False)
        .filter_by(verify_flag=True)
    )

    if search:
        initial_query = initial_query.filter(
            or_(User.name.ilike(f"%{search}%"), User.email_id.ilike(f"%{search}%"))
        )
        count_query = count_query.filter(
            or_(User.name.ilike(f"%{search}%"), User.email_id.ilike(f"%{search}%"))
        )

    if ids:
        initial_query = initial_query.filter(User.id.in_(ids))
        count_query = count_query.filter(User.id.in_(ids))

    if join_types:
        initial_query = initial_query.filter(User.join_type.in_(join_types))
        count_query = count_query.filter(User.join_type.in_(join_types))

    if joined_start_at:
        initial_query = initial_query.filter(User.joined_at >= joined_start_at)
        count_query = count_query.filter(User.joined_at >= joined_start_at)

    if joined_end_at:
        initial_query = initial_query.filter(User.joined_at <= joined_end_at)
        count_query = count_query.filter(User.joined_at <= joined_end_at)

    if status:
        false_condition = literal(False)
        status_active_criteria = (
            not_(
                User.discipline_.any(
                    and_(
                        UserDiscipline.release_flag.is_(False),
                        UserDiscipline.start_at <= utcnow(),
                        UserDiscipline.end_at >= utcnow(),
                    )
                )
            )
            if UserStatusEnum.ACTIVE in status
            else false_condition
        )
        status_disciplined_criteria = (
            User.discipline_.any(
                and_(
                    UserDiscipline.release_flag.is_(False),
                    UserDiscipline.start_at <= utcnow(),
                    UserDiscipline.end_at >= utcnow(),
                )
            )
            if UserStatusEnum.DISCIPLINED in status
            else false_condition
        )
        initial_query = initial_query.filter(
            or_(
                status_active_criteria,
                status_disciplined_criteria,
            )
        )
        count_query = count_query.filter(
            or_(
                status_active_criteria,
                status_disciplined_criteria,
            )
        )

    if report_counts:
        # TODO joony: Implement report_count
        pass

    return get_pagination_list(
        initial_query=initial_query,
        count_query=count_query,
        schema_cls=UserResponse,
        page=page,
        page_size=page_size,
        ordering=ordering,
    )


def get_user(service_id: int, user_id: int) -> UserDetailResponse:
    with session_scope() as session:
        result = session.scalar(
            select(User)
            .filter_by(service_id=service_id)
            .filter_by(id=user_id)
            .filter_by(removed_flag=False)
            .filter_by(withdraw_flag=False)
            .filter_by(verify_flag=True)
        )
        if result is None:
            raise RequestException400(Code.UNKNOWN_MEMBER)
        return UserDetailResponse.model_validate(result)


def get_withdraw_users_by_service_id(
    service_id: int,
    page: int,
    page_size: int,
    ordering: str | None = None,
    search: str | None = None,
    ids: set[int] | None = None,
    withdraw_start_at: AwareDatetime | None = None,
    withdraw_end_at: AwareDatetime | None = None,
    withdraw_reasons: set[str] | None = None,
) -> ListApiResult[UserResponse]:
    initial_query = (
        select(User)
        .filter_by(service_id=service_id)
        .filter_by(removed_flag=False)
        .filter_by(withdraw_flag=True)
        .filter_by(verify_flag=True)
    )
    count_query = (
        select(count(User.id))
        .filter_by(service_id=service_id)
        .filter_by(removed_flag=False)
        .filter_by(withdraw_flag=True)
        .filter_by(verify_flag=True)
    )

    if search:
        initial_query = initial_query.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email_id.ilike(f"%{search}%"),
                User.withdraw_reason.ilike(f"%{search}%"),
            )
        )
        count_query = count_query.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email_id.ilike(f"%{search}%"),
                User.withdraw_reason.ilike(f"%{search}%"),
            )
        )

    if ids:
        initial_query = initial_query.filter(User.id.in_(ids))
        count_query = count_query.filter(User.id.in_(ids))

    if withdraw_start_at:
        initial_query = initial_query.filter(User.withdraw_at >= withdraw_start_at)
        count_query = count_query.filter(User.withdraw_at >= withdraw_start_at)

    if withdraw_end_at:
        initial_query = initial_query.filter(User.withdraw_at <= withdraw_end_at)
        count_query = count_query.filter(User.withdraw_at <= withdraw_end_at)

    if withdraw_reasons:
        initial_query = initial_query.filter(User.withdraw_reason.in_(withdraw_reasons))
        count_query = count_query.filter(User.withdraw_reason.in_(withdraw_reasons))

    return get_pagination_list(
        initial_query=initial_query,
        count_query=count_query,
        schema_cls=UserResponse,
        page=page,
        page_size=page_size,
        ordering=ordering,
    )


def get_code_item_by_service_id(
    service_id: int,
    page: int,
    page_size: int,
    ordering: str | None = None,
    search: str | None = None,
) -> ListApiResult[UserSimple]:
    initial_query = (
        select(User)
        .filter_by(service_id=service_id)
        .filter_by(removed_flag=False)
        .filter_by(withdraw_flag=False)
        .filter_by(verify_flag=True)
        .options(noload("*"))
    )
    count_query = (
        select(count(User.id))
        .filter_by(service_id=service_id)
        .filter_by(removed_flag=False)
        .filter_by(withdraw_flag=False)
        .filter_by(verify_flag=True)
        .options(noload("*"))
    )

    if search:
        initial_query = initial_query.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email_id.ilike(f"%{search}%"),
            )
        )
        count_query = count_query.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email_id.ilike(f"%{search}%"),
            )
        )

    pagination_list = get_pagination_list(
        initial_query=initial_query,
        count_query=count_query,
        schema_cls=UserSimple,
        page=page,
        page_size=page_size,
        ordering=ordering,
    )

    return ListApiResult[UserSimple](
        page=pagination_list.page,
        page_size=pagination_list.page_size,
        total=pagination_list.total,
        items=[UserSimple.model_validate(x) for x in pagination_list.items],
    )
