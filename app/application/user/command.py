from app.application.user.schema import UserRecovery, UserResponse
from app.application.user.uow import UserRDBUow
from app.common.code import Code
from app.common.exception import RequestException400


def reset_password(
    service_id: int,
    user_id: int,
    operator_id: int,
    uow: UserRDBUow,
) -> None:
    with uow.autocommit():
        user = uow.user_repo.get(user_id)
        if (
            user is None
            or user.service_id != service_id
            or user.removed_flag is True
            or user.withdraw_flag is True
            or user.verify_flag is False
        ):
            raise RequestException400(Code.UNKNOWN_MEMBER)
        user.reset_password(operator_id)
        user.on_password_reset()


def reset_image(
    service_id: int,
    user_id: int,
    operator_id: int,
    uow: UserRDBUow,
) -> None:
    with uow.autocommit():
        user = uow.user_repo.get(user_id)
        if (
            user is None
            or user.service_id != service_id
            or user.removed_flag is True
            or user.withdraw_flag is True
            or user.verify_flag is False
        ):
            raise RequestException400(Code.UNKNOWN_MEMBER)
        user.update_image_url(None, operator_id)
        user.on_updated()


def withdraw_user(
    service_id: int,
    user_id: int,
    operator_id: int,
    uow: UserRDBUow,
) -> None:
    with uow.autocommit():
        user = uow.user_repo.get(user_id)
        if (
            user is None
            or user.service_id != service_id
            or user.removed_flag is True
            or user.withdraw_flag is True
            or user.verify_flag is False
        ):
            raise RequestException400(Code.UNKNOWN_MEMBER)
        user.withdraw(operator_id)
        user.on_withdraw()


def remove_user(
    service_id: int,
    user_id: int,
    operator_id: int,
    uow: UserRDBUow,
) -> None:
    with uow.autocommit():
        user = uow.user_repo.get(user_id)
        if user is None or user.service_id != service_id or user.removed_flag is True:
            raise RequestException400(Code.UNKNOWN_MEMBER)
        user.remove(operator_id)
        user.on_removed()


def recovery_user(
    service_id: int,
    user_id: int,
    data: UserRecovery,
    operator_id: int,
    uow: UserRDBUow,
) -> UserResponse:
    with uow.autocommit():
        user = uow.user_repo.get(user_id)
        if (
            user is None
            or user.service_id != service_id
            or user.removed_flag is True
            or user.withdraw_flag is False
            or user.verify_flag is False
        ):
            raise RequestException400(Code.UNKNOWN_MEMBER)
        user.recovery(data, operator_id)
        return user.on_recovery()
