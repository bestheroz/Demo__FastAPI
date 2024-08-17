from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import AwareDatetime

from app.apdapter.auth import AuthorityChecker, get_operator_id
from app.application.notice.command import remove_notice
from app.application.notice.query import get_notice, get_notices_by_service_id
from app.application.notice.schema import NoticeResponse
from app.application.notice.type import NoticeStatusEnum
from app.application.notice.uow import NoticeRDBUow
from app.application.user.type import AuthorityEnum
from app.common.schema import ListApiResult

notice_router = APIRouter(tags=["게시글"])


def get_uow():
    return NoticeRDBUow()


@notice_router.get(
    "/v1/services/{service_id}/notices/",
    name="게시글 목록 조회",
    dependencies=[
        Depends(AuthorityChecker(AuthorityEnum.POSTING_VIEW)),
    ],
)
def _get_notices(
    service_id: int,
    page: Annotated[int, Query()],
    page_size: Annotated[int, Query()],
    search: Annotated[str | None, Query()] = None,
    created_ids: Annotated[set[int] | None, Query()] = None,
    created_start_at: Annotated[AwareDatetime | None, Query()] = None,
    created_end_at: Annotated[AwareDatetime | None, Query()] = None,
    status_: Annotated[set[NoticeStatusEnum] | None, Query(alias="status")] = None,
) -> ListApiResult[NoticeResponse]:
    return get_notices_by_service_id(
        service_id,
        page,
        page_size,
        "-id",
        search,
        created_ids,
        created_start_at,
        created_end_at,
        status_,
    )


@notice_router.get(
    "/v1/services/{service_id}/notices/{notice_id}",
    name="게시글 상세 조회",
    dependencies=[
        Depends(AuthorityChecker(AuthorityEnum.POSTING_VIEW)),
    ],
)
def _get_notice(
    service_id: int,
    notice_id: int,
) -> NoticeResponse:
    return get_notice(service_id, notice_id)


@notice_router.delete(
    "/v1/services/{service_id}/notices/{notice_id}",
    name="게시글 삭제",
    dependencies=[
        Depends(AuthorityChecker(AuthorityEnum.POSTING_DELETE)),
    ],
    status_code=status.HTTP_204_NO_CONTENT,
)
def _delete_notice(
    service_id: int,
    notice_id: int,
    uow: Annotated[NoticeRDBUow, Depends(get_uow)],
    x_operator_id: Annotated[int, Depends(get_operator_id)],
) -> None:
    remove_notice(service_id, notice_id, x_operator_id, uow)
