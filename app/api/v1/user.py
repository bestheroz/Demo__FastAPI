from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Path, Query, status

from app.dependencies.auth import AuthorityChecker, get_operator, get_user_id
from app.schemas.base import ListResult, Operator, Token
from app.schemas.user import (
    UserChangePassword,
    UserCreate,
    UserListRequest,
    UserLogin,
    UserResponse,
    UserUpdate,
)
from app.services.user import (
    change_password,
    check_login_id,
    create_user,
    get_user,
    get_users,
    login_user,
    logout,
    remove_user,
    renew_token,
    update_user,
)
from app.types.base import AuthorityEnum

user_router = APIRouter(tags=["유저"])


@user_router.get(
    "/v1/users",
    name="리스트 조회",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.USER_VIEW])),
    ],
)
async def _get_users(
    request: Annotated[UserListRequest, Depends()],
) -> ListResult[UserResponse]:
    return await get_users(request)


@user_router.get(
    "/v1/users/check-login-id",
    name="로그인 아이디 중복 확인",
)
async def _check_login_id(login_id: Annotated[str, Query()], user_id: Annotated[int | None, Query()] = None) -> bool:
    return await check_login_id(login_id, user_id)


@user_router.get(
    "/v1/users/renew-token",
    name="유저 토큰 갱신",
    description="*어세스 토큰* 만료 시 *리플래시 토큰* 으로 *어세스 토큰* 을 갱신합니다. "
    "(동시에 여러 사용자가 접속하고 있다면 *리플래시 토큰* 값이 달라서 갱신이 안될 수 있습니다.)",
)
async def _renew_token(
    authorization: str = Header(),
) -> Token:
    return await renew_token(authorization)


@user_router.get(
    "/v1/users/{user_id}",
    name="상세 조회",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.USER_VIEW])),
    ],
)
async def _get_user(user_id: Annotated[int, Path(ge=1)]) -> UserResponse:
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


@user_router.post(
    "/v1/users/login",
    name="유저 로그인",
)
async def _login_user(
    payload: UserLogin,
) -> Token:
    return await login_user(payload)


@user_router.put(
    "/v1/users/{user_id}",
    name="유저 수정",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.USER_EDIT])),
    ],
)
async def _update_user(
    user_id: Annotated[int, Path(ge=1)],
    data: UserUpdate,
    x_operator: Annotated[Operator, Depends(get_operator)],
) -> UserResponse:
    return await update_user(user_id, data, x_operator)


@user_router.patch(
    "/v1/users/{user_id}/password",
    name="비밀번호 변경",
)
async def _change_password(
    user_id: Annotated[int, Path(ge=1)],
    data: UserChangePassword,
    x_operator: Annotated[Operator, Depends(get_operator)],
) -> UserResponse:
    return await change_password(user_id, data, x_operator)


@user_router.delete(
    "/v1/users/logout",
    name="유저 로그아웃",
    description="*리플래시 토큰*을 삭제합니다.",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(AuthorityChecker()),
    ],
)
async def _logout(x_user_id: Annotated[int, Depends(get_user_id)], background_tasks: BackgroundTasks) -> None:
    background_tasks.add_task(logout, x_user_id)


@user_router.delete(
    "/v1/users/{user_id}",
    name="유저 삭제",
    dependencies=[
        Depends(AuthorityChecker([AuthorityEnum.USER_EDIT])),
    ],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def _remove_user(
    user_id: Annotated[int, Path(ge=1)],
    x_operator: Annotated[Operator, Depends(get_operator)],
) -> None:
    await remove_user(user_id, x_operator)
