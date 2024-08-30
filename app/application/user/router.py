from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.apdapter.auth import AuthorityChecker, get_operator
from app.application.user.command import (
    change_password,
    create_user,
    remove_user,
    update_user,
)
from app.application.user.query import (
    get_user,
    get_users,
)
from app.application.user.schema import (
    UserChangePassword,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.common.schema import ListApiResult, Operator
from app.common.type import AuthorityEnum

user_router = APIRouter(tags=["유저"])


@user_router.get(
    "/v1/users",
    name="리스트 조회",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.USER_VIEW])),
    ],
)
async def _get_users(
    page: Annotated[int, Query(example=1)],
    page_size: Annotated[int, Query(example=10)],
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


@user_router.post(
    "/v1/users",
    name="유저 생성",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.USER_EDIT])),
    ],
)
async def _create_user(
    data: UserCreate,
    x_operator: Annotated[Operator, Depends(get_operator)],
) -> UserResponse:
    return await create_user(data, x_operator)


@user_router.put(
    "/v1/users/{user_id}",
    name="유저 수정",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.USER_EDIT])),
    ],
)
async def _update_user(
    user_id: int,
    data: UserUpdate,
    x_operator: Annotated[Operator, Depends(get_operator)],
) -> UserResponse:
    return await update_user(user_id, data, x_operator)


@user_router.patch(
    "/v1/users/{user_id}/password",
    name="비밀번호 변경",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.USER_EDIT])),
    ],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def _change_password(
    user_id: int,
    data: UserChangePassword,
    x_operator: Annotated[Operator, Depends(get_operator)],
) -> None:
    await change_password(user_id, data, x_operator)


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
    x_operator: Annotated[Operator, Depends(get_operator)],
) -> None:
    await remove_user(user_id, x_operator)
