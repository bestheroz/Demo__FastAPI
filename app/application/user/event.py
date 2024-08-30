from collections.abc import Callable

from app.apdapter.event import EventHandler
from app.application.user.schema import UserResponse
from app.common.event import Event


class UserCreated(Event[UserResponse]):
    pass


class UserUpdated(Event[UserResponse]):
    pass


class UserPasswordUpdated(Event[UserResponse]):
    pass


class UserLoggedIn(Event[UserResponse]):
    pass


class UserRemoved(Event[UserResponse]):
    pass


class UserEventHandler(EventHandler):
    def get_handlers(self) -> dict[type[Event], list[Callable]]:
        return {
            UserCreated: [],
            UserUpdated: [],
            UserPasswordUpdated: [],
            UserLoggedIn: [],
            UserRemoved: [],
        }
