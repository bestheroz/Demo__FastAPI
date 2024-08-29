from app.apdapter.uow import CommonRDBUow
from app.application.notice.event import NoticeEventHandler
from app.application.notice.model import Notice
from app.common.code import Code
from app.common.exception import RequestException400


def get_uow():
    return CommonRDBUow[Notice](NoticeEventHandler, Notice)


async def remove_notice(
    notice_id: int,
    operator_id: int,
) -> None:
    with get_uow() as uow, uow.transaction():
        notice = uow.repository.get(notice_id)
        if notice is None:
            raise RequestException400(Code.UNKNOWN_NOTICE)
        notice.remove(operator_id)
        notice.on_removed()
