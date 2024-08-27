from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.apdapter.auth import AuthorityChecker, get_operator_id
from app.application.user.command import (
    remove_user,
    reset_password,
)
from app.application.user.query import (
    get_user,
    get_users,
)
from app.application.user.schema import (
    UserResponse,
)
from app.application.user.uow import UserRDBUow
from app.common.schema import ListApiResult
from app.common.type import AuthorityEnum

user_router = APIRouter(tags=["유저"])


def get_uow():
    return UserRDBUow()


@user_router.get(
    "/v1/users/",
    name="리스트 조회",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.USER_VIEW])),
    ],
)
async def _get_users(
    page: Annotated[int, Query()],
    page_size: Annotated[int, Query()],
    search: Annotated[str | None, Query()] = None,
    ids: Annotated[set[int] | None, Query()] = None,
) -> ListApiResult[UserResponse]:
    return await get_users(
        page,
        page_size,
        "-id",
        search,
        ids,
    )


@user_router.get(
    "/v1/users/{user_id}",
    name="상세 조회",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.USER_VIEW])),
    ],
)
async def _get_user(user_id: int) -> UserResponse:
    return await get_user(user_id)


@user_router.delete(
    "/v1/users/{user_id}/reset-password",
    name="비밀번호 초기화",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.USER_EDIT])),
    ],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def _reset_password(
    user_id: int,
    uow: Annotated[UserRDBUow, Depends(get_uow)],
    x_operator_id: Annotated[int, Depends(get_operator_id)],
) -> None:
    await reset_password(user_id, x_operator_id, uow=uow)


@user_router.delete(
    "/v1/users/{user_id}",
    name="유저 삭제",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.USER_EDIT])),
    ],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def _remove_user(
    user_id: int,
    uow: Annotated[UserRDBUow, Depends(get_uow)],
    x_operator_id: Annotated[int, Depends(get_operator_id)],
) -> None:
    await remove_user(user_id, x_operator_id, uow=uow)
