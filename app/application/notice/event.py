from collections.abc import Callable

from app.apdapter.event import EventHandler
from app.application.notice.schema import NoticeResponse
from app.common.event import Event


class NoticeCreated(Event[NoticeResponse]):
    pass


class NoticeUpdated(Event[NoticeResponse]):
    pass


class NoticeRemoved(Event[NoticeResponse]):
    pass


class NoticeEventHandler(EventHandler):
    def get_handlers(self) -> dict[type[Event], list[Callable]]:
        return {
            NoticeCreated: [],
            NoticeUpdated: [],
            NoticeRemoved: [],
        }
