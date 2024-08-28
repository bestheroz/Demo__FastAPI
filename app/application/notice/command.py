from app.apdapter.uow import CommonRDBUow
from app.application.notice.event import NoticeEventHandler
from app.application.notice.model import Notice
from app.common.code import Code
from app.common.exception import RequestException400

uow = CommonRDBUow[Notice](NoticeEventHandler)


async def remove_notice(
    notice_id: int,
    operator_id: int,
) -> None:
    async with uow.transaction():
        notice = await uow.repository.get(notice_id)
        if notice is None:
            raise RequestException400(Code.UNKNOWN_NOTICE)
        notice.remove(operator_id)
        await notice.on_removed()
