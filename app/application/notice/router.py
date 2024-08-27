from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import AwareDatetime

from app.apdapter.auth import AuthorityChecker, get_operator_id
from app.application.notice.command import remove_notice
from app.application.notice.query import get_notice, get_notices
from app.application.notice.schema import NoticeResponse
from app.application.notice.uow import NoticeRDBUow
from app.common.schema import ListApiResult
from app.common.type import AuthorityEnum

notice_router = APIRouter(tags=["게시글"])


def get_uow():
    return NoticeRDBUow()


@notice_router.get(
    "/v1/notices/",
    name="게시글 목록 조회",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.NOTICE_VIEW])),
    ],
)
async def _get_notices(
    page: Annotated[int, Query()],
    page_size: Annotated[int, Query()],
    search: Annotated[str | None, Query()] = None,
    created_ids: Annotated[set[int] | None, Query()] = None,
    created_start_at: Annotated[AwareDatetime | None, Query()] = None,
    created_end_at: Annotated[AwareDatetime | None, Query()] = None,
) -> ListApiResult[NoticeResponse]:
    return await get_notices(
        page,
        page_size,
        "-id",
        search,
        created_ids,
        created_start_at,
        created_end_at,
    )


@notice_router.get(
    "/v1/notices/{notice_id}",
    name="게시글 상세 조회",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.NOTICE_VIEW])),
    ],
)
async def _get_notice(
    notice_id: int,
) -> NoticeResponse:
    return await get_notice(notice_id)


@notice_router.delete(
    "/v1/notices/{notice_id}",
    name="게시글 삭제",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.NOTICE_EDIT])),
    ],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def _delete_notice(
    notice_id: int,
    uow: Annotated[NoticeRDBUow, Depends(get_uow)],
    x_operator_id: Annotated[int, Depends(get_operator_id)],
) -> None:
    await remove_notice(notice_id, x_operator_id, uow)
