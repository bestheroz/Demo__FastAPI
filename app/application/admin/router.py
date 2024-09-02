from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, status

from app.apdapter.auth import AuthorityChecker, SuperManagerOnly, get_admin_id, get_operator
from app.application.admin.command import (
    change_password,
    check_login_id,
    create_admin,
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
    AdminUpdate,
)
from app.common.schema import ListApiResult, Operator, Token
from app.common.type import AuthorityEnum

admin_router = APIRouter(tags=["관리자"])


@admin_router.get(
    "/v1/admins",
    name="리스트 조회",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.ADMIN_VIEW])),
    ],
)
async def _get_admins(
    page: Annotated[int, Query(example=1)],
    page_size: Annotated[int, Query(example=10)],
) -> ListApiResult[AdminResponse]:
    return await get_admins(
        page,
        page_size,
        "-id",
    )


@admin_router.get(
    "/v1/admins/check-login-id",
    name="로그인 아이디 중복 확인",
)
async def _check_login_id(
    login_id: Annotated[str, Query()],
) -> bool:
    return await check_login_id(login_id)


@admin_router.get(
    "/v1/admins/renew-token",
    name="관리자 토큰 갱신",
    description="*어세스 토큰* 만료 시 *리플래시 토큰* 으로 *어세스 토큰* 을 갱신합니다. "
    "(동시에 여러 사용자가 접속하고 있다면 *리플래시 토큰* 값이 달라서 갱신이 안될 수 있습니다.)",
)
async def _renew_token(
    refresh_token: str = Header(alias="AuthorizationR"),
) -> Token:
    return await renew_token(refresh_token)


@admin_router.get(
    "/v1/admins/{admin_id}",
    name="상세 조회",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.ADMIN_VIEW])),
    ],
)
async def _get_admin(admin_id: int) -> AdminResponse:
    return await get_admin(admin_id)


@admin_router.post(
    "/v1/admins",
    name="관리자 생성",
    dependencies=[
        Depends(SuperManagerOnly()),
    ],
)
async def _create_admin(
    payload: AdminCreate,
    x_operator_id: Annotated[int, Depends(get_admin_id)],
) -> AdminResponse:
    return await create_admin(payload, x_operator_id)


@admin_router.post(
    "/v1/admins/login",
    name="관리자 로그인",
)
async def _login_admin(
    payload: AdminLogin,
) -> Token:
    return await login_admin(payload)


@admin_router.put(
    "/v1/admins/{admin_id}",
    name="관리자 수정",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.ADMIN_EDIT])),
    ],
)
async def _update_admin(
    admin_id: int,
    payload: AdminUpdate,
    x_operator: Annotated[Operator, Depends(get_operator)],
) -> AdminResponse:
    return await update_admin(admin_id, payload, x_operator)


@admin_router.patch(
    "/v1/admins/{admin_id}/password",
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


@admin_router.delete(
    "/v1/admins/logout",
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


@admin_router.delete(
    "/v1/admins/{admin_id}",
    name="관리자 삭제",
    description="(Soft delete)",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(SuperManagerOnly()),
    ],
)
async def _remove_admin(
    admin_id: int,
    x_operator_id: Annotated[int, Depends(get_admin_id)],
) -> None:
    await remove_admin(admin_id, x_operator_id)
