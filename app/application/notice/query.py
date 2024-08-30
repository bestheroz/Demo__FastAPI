from sqlalchemy import select
from sqlalchemy.sql.functions import count

from app.apdapter.orm import session_scope
from app.application.notice.model import Notice
from app.application.notice.schema import NoticeResponse
from app.common.code import Code
from app.common.exception import RequestException400
from app.common.schema import ListApiResult
from app.common.type import UserTypeEnum
from app.utils.pagination import get_pagination_list


async def get_notices(
    page: int,
    page_size: int,
    ordering: str | None = None,
    search: str | None = None,
    created_ids: set[int] | None = None,
) -> ListApiResult[NoticeResponse]:
    initial_query = select(Notice)
    count_query = select(count(Notice.id))

    if search:
        # TODO joony: Implement search
        pass

    if created_ids:
        initial_query = initial_query.filter_by(created_object_type=UserTypeEnum.user).filter(
            Notice.created_by_id.in_(created_ids)
        )
        count_query = count_query.filter_by(created_object_type=UserTypeEnum.user).filter(
            Notice.created_by_id.in_(created_ids)
        )

    return await get_pagination_list(
        initial_query=initial_query,
        count_query=count_query,
        schema_cls=NoticeResponse,
        page=page,
        page_size=page_size,
        ordering=ordering,
    )


async def get_notice(notice_id: int) -> NoticeResponse:
    with session_scope() as session:
        result = session.scalar(select(Notice).filter_by(id=notice_id))
        if result is None:
            raise RequestException400(Code.UNKNOWN_NOTICE)
        return NoticeResponse.model_validate(result)
