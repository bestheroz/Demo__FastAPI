from collections.abc import Callable

from app.apdapter.event import EventHandler
from app.application.user.schema import UserResponse
from app.common.event import Event


class UserRemoved(Event[UserResponse]):
    pass


class UserPasswordReset(Event[UserResponse]):
    pass


class UserUpdated(Event[UserResponse]):
    pass


class UserEventHandler(EventHandler):
    def get_handlers(self) -> dict[type[Event], list[Callable]]:
        return {
            UserPasswordReset: [],
            UserRemoved: [],
            UserUpdated: [],
        }
