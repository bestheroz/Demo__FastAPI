from enum import StrEnum

from fastapi_events.registry.payload_schema import registry as payload_schema

from app.schemas.notice import NoticeResponse


class NoticeEvent(StrEnum):
    NOTICE_CREATED = "NOTICE_CREATED"
    NOTICE_UPDATED = "NOTICE_UPDATED"
    NOTICE_REMOVED = "NOTICE_REMOVED"


@payload_schema.register(event_name=NoticeEvent.NOTICE_CREATED)
class NoticeCreatedEvent(NoticeResponse):
    pass


@payload_schema.register(event_name=NoticeEvent.NOTICE_UPDATED)
class NoticeUpdatedEvent(NoticeResponse):
    pass


@payload_schema.register(event_name=NoticeEvent.NOTICE_REMOVED)
class NoticeRemovedEvent(NoticeResponse):
    pass
