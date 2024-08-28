from app.apdapter.uow import CommonRDBUow
from app.application.user.event import UserEventHandler
from app.application.user.model import User
from app.common.code import Code
from app.common.exception import RequestException400


def get_uow():
    return CommonRDBUow[User](UserEventHandler)


async def reset_password(
    user_id: int,
    operator_id: int,
) -> None:
    async with get_uow() as uow, uow.transaction():
        user = await uow.repository.get(user_id)
        if user is None or user.removed_flag is True:
            raise RequestException400(Code.UNKNOWN_USER)
        user.reset_password(operator_id)
        await user.on_password_reset()


async def remove_user(
    user_id: int,
    operator_id: int,
) -> None:
    async with get_uow() as uow, uow.transaction():
        user = await uow.repository.get(user_id)
        if user is None or user.removed_flag is True:
            raise RequestException400(Code.UNKNOWN_USER)
        user.remove(operator_id)
        await user.on_removed()
