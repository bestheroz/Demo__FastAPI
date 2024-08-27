from app.application.notice.uow import NoticeRDBUow
from app.common.code import Code
from app.common.exception import RequestException400


async def remove_notice(
    notice_id: int,
    operator_id: int,
    uow: NoticeRDBUow,
) -> None:
    async with uow.autocommit():
        notice = await uow.notice_repo.get(notice_id)
        if notice is None:
            raise RequestException400(Code.UNKNOWN_NOTICE)
        notice.remove(operator_id)
        await notice.on_removed()
