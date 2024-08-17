from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import SecretStr

from app.apdapter.auth import AuthorityChecker, get_operator_id
from app.application.admin.account.schema import (
    AdminAccountMarketingTermsCreate,
    AdminAccountToken,
    AdminAccountVerify,
)
from app.application.admin.command import (
    cancel_invitation,
    invite_admin,
    re_send_invitation,
    remove_admin,
    remove_admin_image_url,
    update_admin,
    update_admin_image_url,
    verify_admin,
)
from app.application.admin.query import get_admin, get_admins_by_service_id
from app.application.admin.schema import (
    AdminInvite,
    AdminResponse,
    AdminUpdate,
    AdminVerify,
)
from app.application.admin.uow import AdminRDBUow
from app.application.user.type import AuthorityEnum
from app.common.schema import ImageUrlUpdate, ListApiResult

admin_router = APIRouter(tags=["관리자"])


def get_uow():
    return AdminRDBUow()


@admin_router.get(
    "/v1/services/{service_id}/admin/",
    name="리스트 조회",
    dependencies=[
        Depends(AuthorityChecker(AuthorityEnum.ADMIN_VIEW)),
    ],
)
def _get_admins_by_service_id(
    service_id: int,
    page: Annotated[int, Query()],
    page_size: Annotated[int, Query()],
) -> ListApiResult[AdminResponse]:
    return get_admins_by_service_id(service_id, page, page_size)


@admin_router.get(
    "/v1/services/{service_id}/admin/{admin_id}",
    name="상세 조회",
    dependencies=[
        Depends(AuthorityChecker(AuthorityEnum.ADMIN_VIEW)),
    ],
)
def _get_admin(service_id: int, admin_id: int) -> AdminResponse:
    return get_admin(service_id, admin_id)


@admin_router.post(
    "/v1/services/{service_id}/admin/invite",
    name="관리자 초대",
    description="계정이 없는 경우 계정도 함께 초대 됩니다.",
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(AuthorityChecker(AuthorityEnum.ADMIN_ADD)),
    ],
)
def _invite_admin(
    service_id: int,
    payload: AdminInvite,
    uow: Annotated[AdminRDBUow, Depends(get_uow)],
    x_operator_id: Annotated[int, Depends(get_operator_id)],
) -> AdminResponse:
    return invite_admin(payload, service_id, x_operator_id, uow=uow)


@admin_router.post(
    "/v1/services/{service_id}/admin/{admin_id}/re-invite",
    name="초대 메일 재 발송",
    description="재 발송하게 되면 인증토큰 값이 변경되어 이전에 받은 초대 메일은 사용할 수 없습니다.",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(AuthorityChecker(AuthorityEnum.ADMIN_ADD)),
    ],
)
def _re_send_invitation(
    service_id: int,
    admin_id: int,
    uow: Annotated[AdminRDBUow, Depends(get_uow)],
) -> None:
    return re_send_invitation(service_id, admin_id, uow=uow)


@admin_router.delete(
    "/v1/services/{service_id}/admin/{admin_id}/cancel-invitation",
    name="초대를 취소",
    description="초대를 취소하면 초대된 관리자 정보가 db에서 삭제됩니다.",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(AuthorityChecker(AuthorityEnum.ADMIN_ADD)),
    ],
)
def _cancel_invitation(
    service_id: int,
    admin_id: int,
    uow: Annotated[AdminRDBUow, Depends(get_uow)],
) -> None:
    cancel_invitation(service_id, admin_id, uow=uow)


@admin_router.post(
    "/v1/services/{service_id}/admin/{admin_id}/verify",
    name="관리자 인증",
    description="이미 계정 가입된 관리자가 새로운 서비스에 가입할 때 사용합니다.",
)
def _verify_admin(
    service_id: int,
    admin_id: int,
    payload: AdminVerify,
    uow: Annotated[AdminRDBUow, Depends(get_uow)],
) -> AdminAccountToken:
    return verify_admin(
        service_id,
        admin_id,
        AdminAccountVerify(
            name="",  # 관리자 인증시에는 사용하지 않는 파라미터지만 값을 채워야해서 임의로 넣음
            password=SecretStr(
                ""
            ),  # 관리자 인증시에는 사용하지 않는 파라미터지만 값을 채워야해서 임의로 넣음
            verify_token=payload.verify_token,
            terms=[],  # 관리자 인증시에는 사용하지 않는 파라미터지만 값을 채워야해서 임의로 넣음
            marketing_terms=AdminAccountMarketingTermsCreate(
                email_agree_flag=False,
                sms_agree_flag=False,
                call_agree_flag=False,
                post_agree_flag=False,
            ),  # 관리자 인증시에는 사용하지 않는 파라미터지만 값을 채워야해서 임의로 넣음
        ),
        uow=uow,
    )


@admin_router.post(
    "/v1/services/{service_id}/admin/{admin_id}/verify-join",
    name="관리자 인증 및 계정 가입",
    description="신규 관리자 가입 인증과 함께 새로운 서비스에 가입할 때 사용합니다.",
)
def _verify_join_admin(
    service_id: int,
    admin_id: int,
    payload: AdminAccountVerify,
    uow: Annotated[AdminRDBUow, Depends(get_uow)],
) -> AdminAccountToken:
    return verify_admin(service_id, admin_id, payload, uow)


@admin_router.put(
    "/v1/services/{service_id}/admin/{admin_id}",
    name="관리자 수정",
    dependencies=[
        Depends(AuthorityChecker(AuthorityEnum.ADMIN_EDIT)),
    ],
)
def _update_admin(
    service_id: int,
    admin_id: int,
    payload: AdminUpdate,
    uow: Annotated[AdminRDBUow, Depends(get_uow)],
    x_operator_id: Annotated[int, Depends(get_operator_id)],
) -> AdminResponse:
    return update_admin(service_id, admin_id, payload, x_operator_id, uow)


@admin_router.patch(
    "/v1/services/{service_id}/admin/{admin_id}/image-url",
    name="프로필 이미지 URL 등록/수정",
    dependencies=[
        Depends(AuthorityChecker(AuthorityEnum.ADMIN_EDIT)),
    ],
)
def _update_admin_image_url(
    service_id: int,
    admin_id: int,
    payload: ImageUrlUpdate,
    uow: Annotated[AdminRDBUow, Depends(get_uow)],
    x_operator_id: Annotated[int, Depends(get_operator_id)],
) -> AdminResponse:
    return update_admin_image_url(service_id, admin_id, payload, x_operator_id, uow)


@admin_router.delete(
    "/v1/services/{service_id}/admin/{admin_id}/image-url",
    name="프로필 이미지 URL 삭제",
    dependencies=[
        Depends(AuthorityChecker(AuthorityEnum.ADMIN_EDIT)),
    ],
)
def _remove_admin_image_url(
    service_id: int,
    admin_id: int,
    uow: Annotated[AdminRDBUow, Depends(get_uow)],
    x_operator_id: Annotated[int, Depends(get_operator_id)],
) -> AdminResponse:
    return remove_admin_image_url(service_id, admin_id, x_operator_id, uow)


@admin_router.delete(
    "/v1/services/{service_id}/admin/{admin_id}",
    name="관리자 삭제",
    description="(Soft delete)",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(AuthorityChecker(AuthorityEnum.ADMIN_DELETE)),
    ],
)
def _remove_admin(
    service_id: int,
    admin_id: int,
    uow: Annotated[AdminRDBUow, Depends(get_uow)],
    x_operator_id: Annotated[int, Depends(get_operator_id)],
) -> None:
    remove_admin(service_id, admin_id, x_operator_id, uow)
