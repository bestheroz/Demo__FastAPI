from app.apdapter.uow import CommonRDBUow
from app.application.notice.event import NoticeEventHandler
from app.application.notice.model import Notice
from app.application.notice.schema import NoticeCreate, NoticeResponse
from app.common.code import Code
from app.common.exception import BadRequestException400


def get_uow():
    return CommonRDBUow[Notice](NoticeEventHandler, Notice)


async def create_notice(
    data: NoticeCreate,
    operator_id: int,
) -> NoticeResponse:
    with get_uow() as uow, uow.transaction():
        notice = Notice.new(data, operator_id)
        uow.repository.add(notice)
        return notice.on_created()


async def update_notice(
    notice_id: int,
    data: NoticeCreate,
    operator_id: int,
) -> NoticeResponse:
    with get_uow() as uow, uow.transaction():
        notice = uow.repository.get(notice_id)
        if notice is None:
            raise BadRequestException400(Code.UNKNOWN_NOTICE)
        notice.update(data, operator_id)
        return notice.on_updated()


async def remove_notice(
    notice_id: int,
    operator_id: int,
) -> None:
    with get_uow() as uow, uow.transaction():
        notice = uow.repository.get(notice_id)
        if notice is None:
            raise BadRequestException400(Code.UNKNOWN_NOTICE)
        notice.remove(operator_id)
        notice.on_removed()
