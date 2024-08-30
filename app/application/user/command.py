from app.apdapter.uow import CommonRDBUow
from app.application.user.event import UserEventHandler
from app.application.user.model import User
from app.application.user.schema import UserChangePassword, UserCreate, UserResponse, UserUpdate
from app.common.code import Code
from app.common.exception import RequestException400
from app.common.schema import Operator


def get_uow():
    return CommonRDBUow[User](UserEventHandler, User)


async def create_user(data: UserCreate, operator: Operator) -> UserResponse:
    with get_uow() as uow, uow.transaction():
        user = User.new(data, operator)
        uow.repository.add(user)
        return user.on_created()


async def update_user(user_id: int, data: UserUpdate, operator: Operator) -> UserResponse:
    with get_uow() as uow, uow.transaction():
        user = uow.repository.get(user_id)
        if user is None or user.removed_flag is True:
            raise RequestException400(Code.UNKNOWN_USER)
        user.update(data, operator)
        return user.on_updated()


async def change_password(user_id: int, data: UserChangePassword, operator: Operator) -> None:
    with get_uow() as uow, uow.transaction():
        user = uow.repository.get(user_id)
        if user is None or user.removed_flag is True:
            raise RequestException400(Code.UNKNOWN_USER)
        user.change_password(data, operator)
        user.on_password_updated()


async def remove_user(user_id: int, operator: Operator) -> None:
    with get_uow() as uow, uow.transaction():
        user = uow.repository.get(user_id)
        if user is None or user.removed_flag is True:
            raise RequestException400(Code.UNKNOWN_USER)
        user.remove(operator)
        user.on_removed()
