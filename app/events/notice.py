from fastapi_events.registry.payload_schema import registry as payload_schema

from app.schemas.notice import NoticeResponse


@payload_schema.register(event_name="NoticeCreatedEvent")
class NoticeCreatedEvent(NoticeResponse):
    pass


@payload_schema.register(event_name="NoticeUpdatedEvent")
class NoticeUpdatedEvent(NoticeResponse):
    pass


@payload_schema.register(event_name="NoticeRemovedEvent")
class NoticeRemovedEvent(NoticeResponse):
    pass
