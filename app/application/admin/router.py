from typing import Annotated

from fastapi import APIRouter, Depends, Query, status, Header

from app.apdapter.auth import AuthorityChecker, get_operator_id, get_admin_id
from app.application.admin.command import (
    remove_admin,
    update_admin,
    renew_token,
    logout,
    change_password,
    login_admin,
)
from app.application.admin.query import get_admin, get_admins
from app.application.admin.schema import (
    AdminResponse,
    AdminCreate,
    AdminToken,
    AdminChangePassword,
    AdminLogin,
)
from app.application.admin.uow import AdminRDBUow
from app.common.schema import ListApiResult
from app.common.type import AuthorityEnum

admin_router = APIRouter(tags=["관리자"])


def get_uow():
    return AdminRDBUow()


@admin_router.get(
    "/v1/admin/",
    name="리스트 조회",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.ADMIN_VIEW])),
    ],
)
def _get_admins(
    page: Annotated[int, Query()],
    page_size: Annotated[int, Query()],
) -> ListApiResult[AdminResponse]:
    return get_admins(page, page_size)


@admin_router.get(
    "/v1/admin/{admin_id}",
    name="상세 조회",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.ADMIN_VIEW])),
    ],
)
def _get_admin(admin_id: int) -> AdminResponse:
    return get_admin(admin_id)


@admin_router.put(
    "/v1/admin/{admin_id}",
    name="관리자 수정",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.ADMIN_EDIT])),
    ],
)
def _update_admin(
    admin_id: int,
    payload: AdminCreate,
    uow: Annotated[AdminRDBUow, Depends(get_uow)],
    x_operator_id: Annotated[int, Depends(get_operator_id)],
) -> AdminResponse:
    return update_admin(admin_id, payload, x_operator_id, uow)


@admin_router.delete(
    "/v1/admin/{admin_id}",
    name="관리자 삭제",
    description="(Soft delete)",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.ADMIN_EDIT])),
    ],
)
def _remove_admin(
    admin_id: int,
    uow: Annotated[AdminRDBUow, Depends(get_uow)],
    x_operator_id: Annotated[int, Depends(get_operator_id)],
) -> None:
    remove_admin(admin_id, x_operator_id, uow)


@admin_router.get(
    "/v1/admin/renew-token",
    name="관리자 토큰 갱신",
    description="*어세스 토큰* 만료 시 *리플래시 토큰* 으로 *어세스 토큰* 을 갱신합니다. "
    "(동시에 여러 사용자가 접속하고 있다면 *리플래시 토큰* 값이 달라서 갱신이 안될 수 있습니다.)",
)
def _renew_token(
    uow: Annotated[AdminRDBUow, Depends(get_uow)],
    refresh_token: str = Header(alias="AuthorizationR"),
) -> AdminToken:
    return renew_token(refresh_token, uow)


@admin_router.post(
    "/v1/admin/login",
    name="관리자 로그인",
)
def _login_admin(
    payload: AdminLogin,
    uow: Annotated[AdminRDBUow, Depends(get_uow)],
) -> AdminToken:
    return login_admin(payload, uow)


@admin_router.delete(
    "/v1/admin/logout",
    name="관리자 로그아웃",
    description="*리플래시 토큰*을 삭제합니다.",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(AuthorityChecker()),
    ],
)
def _logout(
    uow: Annotated[AdminRDBUow, Depends(get_uow)],
    x_admin_id: Annotated[int, Depends(get_admin_id)],
) -> None:
    logout(x_admin_id, uow)


@admin_router.patch(
    "/v1/admin/{admin_id}/change-password",
    name="관리자 비밀번호 변경",
    dependencies=[
        Depends(AuthorityChecker()),
    ],
)
def _change_password(
    admin_id: int,
    payload: AdminChangePassword,
    uow: Annotated[AdminRDBUow, Depends(get_uow)],
) -> AdminResponse:
    return change_password(admin_id, payload, uow)
