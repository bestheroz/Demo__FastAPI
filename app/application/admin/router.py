from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, status

from app.apdapter.auth import AuthorityChecker, get_admin_id, get_operator_id
from app.application.admin.command import (
    change_password,
    login_admin,
    logout,
    remove_admin,
    renew_token,
    update_admin,
)
from app.application.admin.query import get_admin, get_admins
from app.application.admin.schema import (
    AdminChangePassword,
    AdminCreate,
    AdminLogin,
    AdminResponse,
    AdminToken,
)
from app.common.schema import ListApiResult
from app.common.type import AuthorityEnum

admin_router = APIRouter(tags=["관리자"])


@admin_router.get(
    "/v1/admin",
    name="리스트 조회",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.ADMIN_VIEW])),
    ],
)
async def _get_admins(
    page: Annotated[int, Query(example=1)],
    page_size: Annotated[int, Query(example=10)],
) -> ListApiResult[AdminResponse]:
    return await get_admins(page, page_size)


@admin_router.get(
    "/v1/admin/renew-token",
    name="관리자 토큰 갱신",
    description="*어세스 토큰* 만료 시 *리플래시 토큰* 으로 *어세스 토큰* 을 갱신합니다. "
    "(동시에 여러 사용자가 접속하고 있다면 *리플래시 토큰* 값이 달라서 갱신이 안될 수 있습니다.)",
)
async def _renew_token(
    refresh_token: str = Header(alias="AuthorizationR"),
) -> AdminToken:
    return await renew_token(refresh_token)


@admin_router.post(
    "/v1/admin/login",
    name="관리자 로그인",
)
async def _login_admin(
    payload: AdminLogin,
) -> AdminToken:
    return await login_admin(payload)


@admin_router.delete(
    "/v1/admin/logout",
    name="관리자 로그아웃",
    description="*리플래시 토큰*을 삭제합니다.",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(AuthorityChecker()),
    ],
)
async def _logout(
    x_admin_id: Annotated[int, Depends(get_admin_id)],
) -> None:
    await logout(x_admin_id)


@admin_router.get(
    "/v1/admin/{admin_id}",
    name="상세 조회",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.ADMIN_VIEW])),
    ],
)
async def _get_admin(admin_id: int) -> AdminResponse:
    return await get_admin(admin_id)


@admin_router.put(
    "/v1/admin/{admin_id}",
    name="관리자 수정",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.ADMIN_EDIT])),
    ],
)
async def _update_admin(
    admin_id: int,
    payload: AdminCreate,
    x_operator_id: Annotated[int, Depends(get_operator_id)],
) -> AdminResponse:
    return await update_admin(admin_id, payload, x_operator_id)


@admin_router.delete(
    "/v1/admin/{admin_id}",
    name="관리자 삭제",
    description="(Soft delete)",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.ADMIN_EDIT])),
    ],
)
async def _remove_admin(
    admin_id: int,
    x_operator_id: Annotated[int, Depends(get_operator_id)],
) -> None:
    await remove_admin(admin_id, x_operator_id)


@admin_router.patch(
    "/v1/admin/{admin_id}/change-password",
    name="관리자 비밀번호 변경",
    dependencies=[
        Depends(AuthorityChecker()),
    ],
)
async def _change_password(
    admin_id: int,
    payload: AdminChangePassword,
) -> AdminResponse:
    return await change_password(admin_id, payload)
