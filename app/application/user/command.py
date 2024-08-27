from app.application.user.uow import UserRDBUow
from app.common.code import Code
from app.common.exception import RequestException400


def reset_password(
    user_id: int,
    operator_id: int,
    uow: UserRDBUow,
) -> None:
    with uow.autocommit():
        user = uow.user_repo.get(user_id)
        if user is None or user.removed_flag is True:
            raise RequestException400(Code.UNKNOWN_USER)
        user.reset_password(operator_id)
        user.on_password_reset()


def remove_user(
    user_id: int,
    operator_id: int,
    uow: UserRDBUow,
) -> None:
    with uow.autocommit():
        user = uow.user_repo.get(user_id)
        if user is None or user.removed_flag is True:
            raise RequestException400(Code.UNKNOWN_USER)
        user.remove(operator_id)
        user.on_removed()
