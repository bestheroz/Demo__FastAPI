from sqlalchemy import select
from sqlalchemy.sql.functions import count

from app.core.code import Code
from app.core.exception import BadRequestException400
from app.dependencies.database import transactional
from app.models.notice import Notice
from app.schemas.base import ListResult
from app.schemas.notice import NoticeCreate, NoticeResponse
from app.utils.pagination import get_pagination_list


async def get_notices(
    page: int,
    page_size: int,
    ordering: str | None = None,
    search: str | None = None,
    use_flag: bool | None = None,
) -> ListResult[NoticeResponse]:
    with transactional(readonly=True) as session:
        initial_query = select(Notice).filter_by(removed_flag=False)
        count_query = select(count(Notice.id)).filter_by(removed_flag=False)

        if search:
            # TODO joony: Implement search
            pass

        if use_flag:
            initial_query = initial_query.filter_by(use_flag=use_flag)
            count_query = count_query.filter_by(use_flag=use_flag)

        return await get_pagination_list(
            session=session,
            initial_query=initial_query,
            count_query=count_query,
            schema_cls=NoticeResponse,
            page=page,
            page_size=page_size,
            ordering=ordering,
        )


async def get_notice(notice_id: int) -> NoticeResponse:
    with transactional(readonly=True) as session:
        result = session.scalar(select(Notice).filter_by(id=notice_id))
        if result is None:
            raise BadRequestException400(Code.UNKNOWN_NOTICE)
        return NoticeResponse.model_validate(result)


async def create_notice(
    data: NoticeCreate,
    operator_id: int,
) -> NoticeResponse:
    with transactional() as session:
        notice = Notice.new(data, operator_id)
        session.add(notice)
        return notice.on_created()


async def update_notice(
    notice_id: int,
    data: NoticeCreate,
    operator_id: int,
) -> NoticeResponse:
    with transactional() as session:
        notice = session.scalar(select(Notice).filter_by(id=notice_id))
        if notice is None:
            raise BadRequestException400(Code.UNKNOWN_NOTICE)
        notice.update(data, operator_id)
        return notice.on_updated()


async def remove_notice(
    notice_id: int,
    operator_id: int,
) -> None:
    with transactional() as session:
        notice = session.scalar(select(Notice).filter_by(id=notice_id))
        if notice is None:
            raise BadRequestException400(Code.UNKNOWN_NOTICE)
        notice.remove(operator_id)
        notice.on_removed()
