from collections.abc import Callable

from app.apdapter.event import EventHandler
from app.application.user.handler import (
    append_user_history,
    send_email_for_user_password_reset,
)
from app.application.user.schema import UserEvent, UserResponse
from app.common.event import Event


class UserWithdrew(Event[UserResponse]):
    pass


class UserRemoved(Event[UserResponse]):
    pass


class UserRecovered(Event[UserResponse]):
    pass


class UserPasswordReset(Event[UserEvent]):
    pass


class UserUpdated(Event[UserResponse]):
    pass


class UserEventHandler(EventHandler):
    def get_handlers(self) -> dict[type[Event], list[Callable]]:
        return {
            UserWithdrew: [append_user_history],
            UserPasswordReset: [
                append_user_history,
                send_email_for_user_password_reset,
            ],
            UserRemoved: [append_user_history],
            UserRecovered: [append_user_history],
            UserUpdated: [append_user_history],
        }
