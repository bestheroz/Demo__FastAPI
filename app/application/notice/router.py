from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.apdapter.auth import AuthorityChecker, get_admin_id
from app.application.notice.command import create_notice, remove_notice, update_notice
from app.application.notice.query import get_notice, get_notices
from app.application.notice.schema import NoticeCreate, NoticeResponse
from app.common.schema import ListApiResult
from app.common.type import AuthorityEnum

notice_router = APIRouter(tags=["공지사항"])


@notice_router.get(
    "/v1/notices",
    name="공지사항 목록 조회",
)
async def _get_notices(
    page: Annotated[int, Query(example=1)],
    page_size: Annotated[int, Query(example=10)],
    search: Annotated[str | None, Query()] = None,
    created_ids: Annotated[set[int] | None, Query()] = None,
) -> ListApiResult[NoticeResponse]:
    return await get_notices(
        page,
        page_size,
        "-id",
        search,
        created_ids,
    )


@notice_router.get(
    "/v1/notices/{notice_id}",
    name="공지사항 상세 조회",
)
async def _get_notice(
    notice_id: int,
) -> NoticeResponse:
    return await get_notice(notice_id)


@notice_router.post(
    "/v1/notices",
    name="공지사항 등록",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.NOTICE_EDIT])),
    ],
    response_model=NoticeResponse,
)
async def _create_notice(
    data: NoticeCreate,
    x_operator_id: Annotated[int, Depends(get_admin_id)],
) -> NoticeResponse:
    return await create_notice(data, x_operator_id)


@notice_router.put(
    "/v1/notices/{notice_id}",
    name="공지사항 수정",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.NOTICE_EDIT])),
    ],
    response_model=NoticeResponse,
)
async def _update_notice(
    notice_id: int,
    data: NoticeCreate,
    x_operator_id: Annotated[int, Depends(get_admin_id)],
) -> NoticeResponse:
    return await update_notice(notice_id, data, x_operator_id)


@notice_router.delete(
    "/v1/notices/{notice_id}",
    name="공지사항 삭제",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.NOTICE_EDIT])),
    ],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def _delete_notice(
    notice_id: int,
    x_operator_id: Annotated[int, Depends(get_admin_id)],
) -> None:
    await remove_notice(notice_id, x_operator_id)
