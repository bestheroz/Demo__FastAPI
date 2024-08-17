from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import AwareDatetime

from app.apdapter.auth import AuthorityChecker, get_operator_id
from app.application.user.command import (
    recovery_user,
    remove_user,
    reset_image,
    reset_password,
    withdraw_user,
)
from app.application.user.file import download_excel
from app.application.user.query import (
    get_code_item_by_service_id,
    get_user,
    get_users_by_service_id,
    get_withdraw_users_by_service_id,
)
from app.application.user.schema import (
    UserDetailResponse,
    UserRecovery,
    UserResponse,
    UserSimple,
)
from app.application.user.type import UserJoinTypeEnum, UserStatusEnum
from app.application.user.uow import UserRDBUow
from app.application.user.type import AuthorityEnum
from app.common.schema import ListApiResult

user_router = APIRouter(tags=["유저"])


def get_uow():
    return UserRDBUow()


@user_router.get(
    "/v1/services/{service_id}/users/",
    name="리스트 조회",
    dependencies=[
        Depends(AuthorityChecker(AuthorityEnum.MEMBER_VIEW)),
    ],
)
def _get_users_by_service_id(
    service_id: int,
    page: Annotated[int, Query()],
    page_size: Annotated[int, Query()],
    search: Annotated[str | None, Query()] = None,
    ids: Annotated[set[int] | None, Query()] = None,
    join_types: Annotated[set[UserJoinTypeEnum] | None, Query()] = None,
    joined_start_at: Annotated[AwareDatetime | None, Query()] = None,
    joined_end_at: Annotated[AwareDatetime | None, Query()] = None,
    status_: Annotated[set[UserStatusEnum] | None, Query(alias="status")] = None,
    report_counts: Annotated[set[int] | None, Query()] = None,
) -> ListApiResult[UserResponse]:
    return get_users_by_service_id(
        service_id,
        page,
        page_size,
        "-id",
        search,
        ids,
        join_types,
        joined_start_at,
        joined_end_at,
        status_,
        report_counts,
    )


@user_router.get(
    "/v1/services/{service_id}/users/download-excel",
    name="엑셀 다운로드",
    dependencies=[
        Depends(AuthorityChecker(AuthorityEnum.MEMBER_VIEW)),
    ],
)
async def _download_excel(
    service_id: int,
    filename: Annotated[
        str | None,
        Query(description="파일명 지정(생략시: 유저목록__{now_iso8601_string()}.xlsx"),
    ] = None,
    ids: Annotated[set[int] | None, Query(description="ID 리스트")] = None,
):
    ids = ids or set()
    return await download_excel(service_id, filename, ids)


@user_router.get(
    "/v1/services/{service_id}/users/simple-items/",
    name="유저 ID, 이름 리스트 조회",
    dependencies=[
        Depends(AuthorityChecker()),
    ],
)
def _get_code_item_by_service_id(
    service_id: int,
    page: Annotated[int, Query()],
    page_size: Annotated[int, Query()],
    search: Annotated[str | None, Query()] = None,
) -> ListApiResult[UserSimple]:
    return get_code_item_by_service_id(service_id, page, page_size, "name", search)


@user_router.get(
    "/v1/services/{service_id}/users/{user_id}",
    name="상세 조회",
    dependencies=[
        Depends(AuthorityChecker(AuthorityEnum.MEMBER_VIEW)),
    ],
)
def _get_user(service_id: int, user_id: int) -> UserDetailResponse:
    return get_user(service_id, user_id)


@user_router.delete(
    "/v1/services/{service_id}/users/{user_id}/reset-password",
    name="비밀번호 초기화",
    dependencies=[
        Depends(AuthorityChecker(AuthorityEnum.MEMBER_EDIT)),
    ],
    status_code=status.HTTP_204_NO_CONTENT,
)
def _reset_password(
    service_id: int,
    user_id: int,
    uow: Annotated[UserRDBUow, Depends(get_uow)],
    x_operator_id: Annotated[int, Depends(get_operator_id)],
) -> None:
    reset_password(service_id, user_id, x_operator_id, uow=uow)


@user_router.delete(
    "/v1/services/{service_id}/users/{user_id}/reset-image",
    name="비밀번호 초기화",
    dependencies=[
        Depends(AuthorityChecker(AuthorityEnum.MEMBER_EDIT)),
    ],
    status_code=status.HTTP_204_NO_CONTENT,
)
def _reset_image(
    service_id: int,
    user_id: int,
    uow: Annotated[UserRDBUow, Depends(get_uow)],
    x_operator_id: Annotated[int, Depends(get_operator_id)],
) -> None:
    reset_image(service_id, user_id, x_operator_id, uow=uow)


@user_router.delete(
    "/v1/services/{service_id}/users/{user_id}/withdraw",
    name="유저 탈퇴",
    dependencies=[
        Depends(AuthorityChecker(AuthorityEnum.MEMBER_WITHDRAW)),
    ],
    status_code=status.HTTP_204_NO_CONTENT,
)
def _withdraw_user(
    service_id: int,
    user_id: int,
    uow: Annotated[UserRDBUow, Depends(get_uow)],
    x_operator_id: Annotated[int, Depends(get_operator_id)],
) -> None:
    withdraw_user(service_id, user_id, x_operator_id, uow=uow)


@user_router.delete(
    "/v1/services/{service_id}/users/{user_id}",
    name="유저 삭제",
    dependencies=[
        Depends(AuthorityChecker(AuthorityEnum.MEMBER_DELETE)),
    ],
    status_code=status.HTTP_204_NO_CONTENT,
)
def _remove_user(
    service_id: int,
    user_id: int,
    uow: Annotated[UserRDBUow, Depends(get_uow)],
    x_operator_id: Annotated[int, Depends(get_operator_id)],
) -> None:
    remove_user(service_id, user_id, x_operator_id, uow=uow)


@user_router.get(
    "/v1/services/{service_id}/withdraw-users/",
    name="탈퇴 유저 리스트 조회",
    dependencies=[
        Depends(AuthorityChecker(AuthorityEnum.MEMBER_WITHDRAW_VIEW)),
    ],
)
def _get_withdraw_users_by_service_id(
    service_id: int,
    page: Annotated[int, Query()],
    page_size: Annotated[int, Query()],
    search: Annotated[str | None, Query()] = None,
    ids: Annotated[set[int] | None, Query()] = None,
    withdraw_start_at: Annotated[AwareDatetime | None, Query()] = None,
    withdraw_end_at: Annotated[AwareDatetime | None, Query()] = None,
    withdraw_reasons: Annotated[set[str] | None, Query()] = None,
) -> ListApiResult[UserResponse]:
    return get_withdraw_users_by_service_id(
        service_id,
        page,
        page_size,
        "-id",
        search,
        ids,
        withdraw_start_at,
        withdraw_end_at,
        withdraw_reasons,
    )


@user_router.post(
    "/v1/services/{service_id}/withdraw-users/{user_id}/recovery",
    name="탈퇴 유저 복구",
    dependencies=[
        Depends(AuthorityChecker(AuthorityEnum.MEMBER_WITHDRAW_RECOVERY)),
    ],
)
def _recovery_user(
    service_id: int,
    user_id: int,
    payload: UserRecovery,
    uow: Annotated[UserRDBUow, Depends(get_uow)],
    x_operator_id: Annotated[int, Depends(get_operator_id)],
) -> UserResponse:
    return recovery_user(service_id, user_id, payload, x_operator_id, uow)
