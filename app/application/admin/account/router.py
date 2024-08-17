from typing import Annotated

from fastapi import APIRouter, Depends, Header, status

from app.apdapter.auth import AuthorityChecker, get_admin_account_id, get_operator_id
from app.application.admin.account.command import (
    change_password,
    change_profile,
    create_admin_account,
    login_admin_account,
    logout,
    remove_admin_account,
    remove_admin_account_image_url,
    remove_temp,
    renew_token,
    update_admin_account_image_url,
    verify_admin_account,
)
from app.application.admin.account.query import get_admin_account
from app.application.admin.account.schema import (
    AdminChangePassword,
    AdminAccountChangeProfile,
    AdminAccountCreate,
    AdminLogin,
    AdminAccountResponse,
    AdminAccountToken,
    AdminAccountVerify,
)
from app.application.admin.account.uow import AdminAccountRDBUow
from app.common.schema import ImageUrlUpdate

admin_account_router = APIRouter(tags=["관리자 계정"])


def get_uow():
    return AdminAccountRDBUow()


@admin_account_router.delete(
    "/v1/admin-account/temp/{email_id}",
    name="(WARNING 임시::관리자 계정 생성 테스트용)관리자 계정 삭제",
    description="여러번의 계정 생성, 계정 초대 테스트 해보시라고 임시로 만든 API입니다. 테스트 이후 삭제됩니다.",
    deprecated=True,
    status_code=status.HTTP_204_NO_CONTENT,
)
def _remove_temp(
    email_id: str,
    uow: Annotated[AdminAccountRDBUow, Depends(get_uow)],
) -> None:
    remove_temp(email_id, uow)


@admin_account_router.post(
    "/v1/admin-account",
    name="관리자 계정 생성 요청(인증메일)",
    description="생성 직후 인증 이메일이 발송되며 인증을 진행해야 관리자 계정을 사용 가능합니다.",
    status_code=status.HTTP_201_CREATED,
)
def _create_admin_account(
    payload: AdminAccountCreate,
    uow: Annotated[AdminAccountRDBUow, Depends(get_uow)],
) -> AdminAccountResponse:
    return create_admin_account(payload, uow)


@admin_account_router.post(
    "/v1/admin-account/{admin_account_id}/verify",
    name="관리자 계정 인증",
    description="인트로페이지에서 관리자 계정 생성 시 전달 받은 토큰으로 가입 인증을 진행합니다.",
)
def _verify_admin_account(
    admin_account_id: int,
    payload: AdminAccountVerify,
    uow: Annotated[AdminAccountRDBUow, Depends(get_uow)],
) -> AdminAccountToken:
    return verify_admin_account(admin_account_id, payload, uow)


@admin_account_router.get(
    "/v1/admin-account/renew-token",
    name="관리자 계정 토큰 갱신",
    description="*어세스 토큰* 만료 시 *리플래시 토큰* 으로 *어세스 토큰* 을 갱신합니다. "
    "(동시에 여러 사용자가 접속하고 있다면 *리플래시 토큰* 값이 달라서 갱신이 안될 수 있습니다.)",
)
def _renew_token(
    uow: Annotated[AdminAccountRDBUow, Depends(get_uow)],
    refresh_token: str = Header(alias="AuthorizationR"),
) -> AdminAccountToken:
    return renew_token(refresh_token, uow)


@admin_account_router.delete(
    "/v1/admin-account/logout",
    name="관리자 계정 로그아웃",
    description="*리플래시 토큰*을 삭제합니다.",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(AuthorityChecker()),
    ],
)
def _logout(
    uow: Annotated[AdminAccountRDBUow, Depends(get_uow)],
    x_admin_account_id: Annotated[int, Depends(get_admin_account_id)],
) -> None:
    logout(x_admin_account_id, uow)


@admin_account_router.get(
    "/v1/admin-account/{admin_account_id}",
    name="관리자 계정 상세 조회",
    dependencies=[
        Depends(AuthorityChecker()),
    ],
)
def _get_admin_account(admin_account_id: int) -> AdminAccountResponse:
    return get_admin_account(admin_account_id)


@admin_account_router.patch(
    "/v1/admin-account/{admin_account_id}/change-password",
    name="관리자 계정 비밀번호 변경",
    dependencies=[
        Depends(AuthorityChecker()),
    ],
)
def _change_password(
    admin_account_id: int,
    payload: AdminChangePassword,
    uow: Annotated[AdminAccountRDBUow, Depends(get_uow)],
) -> AdminAccountResponse:
    return change_password(admin_account_id, payload, uow)


@admin_account_router.patch(
    "/v1/admin-account/{admin_account_id}/change-profile",
    name="관리자 계정 프로필 업데이트",
    dependencies=[
        Depends(AuthorityChecker()),
    ],
)
def _change_profile(
    admin_account_id: int,
    payload: AdminAccountChangeProfile,
    uow: Annotated[AdminAccountRDBUow, Depends(get_uow)],
) -> AdminAccountResponse:
    return change_profile(admin_account_id, payload, uow)


@admin_account_router.post(
    "/v1/admin-account/login",
    name="관리자 계정 로그인",
)
def _login_admin_account(
    payload: AdminLogin,
    uow: Annotated[AdminAccountRDBUow, Depends(get_uow)],
) -> AdminAccountToken:
    return login_admin_account(payload, uow)


@admin_account_router.patch(
    "/v1/admin-account/{admin_account_id}/image-url",
    name="프로필 이미지 URL 등록/수정",
    dependencies=[
        Depends(AuthorityChecker()),
    ],
)
def _update_admin_account_image_url(
    admin_account_id: int,
    payload: ImageUrlUpdate,
    uow: Annotated[AdminAccountRDBUow, Depends(get_uow)],
) -> AdminAccountResponse:
    return update_admin_account_image_url(admin_account_id, payload, uow)


@admin_account_router.delete(
    "/v1/admin-account/{admin_account_id}/image-url",
    name="프로필 이미지 URL 삭제",
    dependencies=[
        Depends(AuthorityChecker()),
    ],
)
def _remove_admin_account_image_url(
    admin_account_id: int,
    uow: Annotated[AdminAccountRDBUow, Depends(get_uow)],
) -> AdminAccountResponse:
    return remove_admin_account_image_url(admin_account_id, uow)


@admin_account_router.delete(
    "/v1/admin-account/{admin_account_id}",
    name="관리자 계정 삭제",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(AuthorityChecker()),
    ],
)
def _remove_admin_account(
    admin_account_id: int,
    x_operator_id: Annotated[int, Depends(get_operator_id)],
    uow: Annotated[AdminAccountRDBUow, Depends(get_uow)],
) -> None:
    remove_admin_account(admin_account_id, x_operator_id, uow=uow)
