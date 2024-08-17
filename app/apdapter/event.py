import inspect
from abc import ABC, abstractmethod
from collections.abc import Callable

from sentry_sdk import capture_exception
from structlog import get_logger

from app.common.event import Event

log = get_logger()


class EventHandler(ABC):
    @abstractmethod
    def get_handlers(self) -> dict[type[Event], list[Callable]]: ...

    def handle(self, event: Event, uow=None, session=None):
        try:
            handlers = self.get_handlers()[type(event)]
        except KeyError as exc:
            capture_exception(exc)
            log.error(f"No handler for event {type(event)}")
            log.exception(exc)
            return

        for handler in handlers:
            params = inspect.signature(handler).parameters
            # for injecting parameters
            kwargs = {}
            if params.get("session"):
                kwargs["session"] = session
            if params.get("uow"):
                kwargs["uow"] = uow

            handler(event, **kwargs)
