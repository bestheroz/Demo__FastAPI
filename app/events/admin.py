from fastapi_events.registry.payload_schema import registry as payload_schema

from app.schemas.admin import AdminResponse


@payload_schema.register(event_name="AdminCreatedEvent")
class AdminCreatedEvent(AdminResponse):
    pass


@payload_schema.register(event_name="AdminUpdatedEvent")
class AdminUpdatedEvent(AdminResponse):
    pass


@payload_schema.register(event_name="AdminPasswordChangedEvent")
class AdminPasswordChangedEvent(AdminResponse):
    pass


@payload_schema.register(event_name="AdminLoggedInEvent")
class AdminLoggedInEvent(AdminResponse):
    pass


@payload_schema.register(event_name="AdminRemovedEvent")
class AdminRemovedEvent(AdminResponse):
    pass
