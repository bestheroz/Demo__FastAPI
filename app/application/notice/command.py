from app.application.notice.uow import NoticeRDBUow
from app.common.code import Code
from app.common.exception import RequestException400


def remove_notice(
    service_id: int,
    notice_id: int,
    operator_id: int,
    uow: NoticeRDBUow,
) -> None:
    with uow.autocommit():
        notice = uow.notice_repo.get(notice_id)
        if notice is None or notice.service_id != service_id:
            raise RequestException400(Code.UNKNOWN_POSTING)
        notice.remove(operator_id)
        notice.on_removed()
