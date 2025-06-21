from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dependencies.auth import AuthorityChecker, get_admin_id
from app.schemas.base import ListResult
from app.schemas.notice import NoticeCreate, NoticeListRequest, NoticeResponse
from app.services.notice import create_notice, get_notice, get_notices, remove_notice, update_notice
from app.types.base import AuthorityEnum

notice_router = APIRouter(tags=["공지사항"])


@notice_router.get(
    "/v1/notices",
    name="공지사항 목록 조회",
)
async def _get_notices(
    request: Annotated[NoticeListRequest, Depends()],
) -> ListResult[NoticeResponse]:
    return await get_notices(request)


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
