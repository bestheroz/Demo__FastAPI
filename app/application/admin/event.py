from collections.abc import Callable

from app.apdapter.event import EventHandler
from app.application.admin.schema import AdminResponse
from app.common.event import Event


class AdminCreated(Event[AdminResponse]):
    pass


class AdminUpdated(Event[AdminResponse]):
    pass


class AdminRemoved(Event[AdminResponse]):
    pass


class AdminEventHandler(EventHandler):
    def get_handlers(self) -> dict[type[Event], list[Callable]]:
        return {
            AdminCreated: [],
            AdminUpdated: [],
            AdminRemoved: [],
        }
