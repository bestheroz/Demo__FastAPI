from pydantic import AwareDatetime
from sqlalchemy import and_, literal, or_, select
from sqlalchemy.sql.functions import count

from app.apdapter.orm import session_scope
from app.application.notice.model import Notice
from app.application.notice.schema import NoticeResponse
from app.application.notice.type import NoticeStatusEnum
from app.common.code import Code
from app.common.exception import RequestException400
from app.common.schema import ListApiResult
from app.common.type import UserTypeEnum
from app.utils.pagination import get_pagination_list


def get_notices_by_service_id(
    service_id: int,
    page: int,
    page_size: int,
    ordering: str | None = None,
    search: str | None = None,
    created_ids: set[int] | None = None,
    created_start_at: AwareDatetime | None = None,
    created_end_at: AwareDatetime | None = None,
    status: set[NoticeStatusEnum] | None = None,
) -> ListApiResult[NoticeResponse]:
    initial_query = select(Notice).filter_by(service_id=service_id)
    count_query = select(count(Notice.id)).filter_by(service_id=service_id)

    if search:
        # TODO joony: Implement search
        pass

    if created_ids:
        initial_query = initial_query.filter_by(
            created_object_type=UserTypeEnum.user
        ).filter(Notice.created_by_id.in_(created_ids))
        count_query = count_query.filter_by(
            created_object_type=UserTypeEnum.user
        ).filter(Notice.created_by_id.in_(created_ids))

    if created_start_at:
        initial_query = initial_query.filter(Notice.created_at >= created_start_at)
        count_query = count_query.filter(Notice.created_at >= created_start_at)

    if created_end_at:
        initial_query = initial_query.filter(Notice.created_at <= created_end_at)
        count_query = count_query.filter(Notice.created_at <= created_end_at)

    if status:
        false_condition = literal(False)
        status_active_criteria = (
            Notice.removed_flag.is_(False)
            if NoticeStatusEnum.ACTIVE in status
            else false_condition
        )
        status_remove_by_admin_criteria = (
            and_(
                Notice.removed_flag.is_(True),
                Notice.updated_object_type == UserTypeEnum.admin,
            )
            if NoticeStatusEnum.REMOVED_BY_ADMIN in status
            else false_condition
        )
        status_remove_by_user_criteria = (
            and_(
                Notice.removed_flag.is_(True),
                Notice.updated_object_type == UserTypeEnum.user,
            )
            if NoticeStatusEnum.REMOVED_BY_MEMBER in status
            else false_condition
        )
        initial_query = initial_query.filter(
            or_(
                status_active_criteria,
                status_remove_by_admin_criteria,
                status_remove_by_user_criteria,
            )
        )
        count_query = count_query.filter(
            or_(
                status_active_criteria,
                status_remove_by_admin_criteria,
                status_remove_by_user_criteria,
            )
        )

    return get_pagination_list(
        initial_query=initial_query,
        count_query=count_query,
        schema_cls=NoticeResponse,
        page=page,
        page_size=page_size,
        ordering=ordering,
    )


def get_notice(service_id: int, notice_id: int) -> NoticeResponse:
    with session_scope() as session:
        result = session.scalar(
            select(Notice).filter_by(service_id=service_id).filter_by(id=notice_id)
        )
        if result is None:
            raise RequestException400(Code.UNKNOWN_NOTICE)
        return NoticeResponse.model_validate(result)
