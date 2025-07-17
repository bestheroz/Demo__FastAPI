from enum import StrEnum

from fastapi_events.registry.payload_schema import registry as payload_schema

from app.schemas.admin import AdminResponse


class AdminEvent(StrEnum):
    ADMIN_CREATED = "ADMIN_CREATED"
    ADMIN_UPDATED = "ADMIN_UPDATED"
    ADMIN_PASSWORD_CHANGED = "ADMIN_PASSWORD_CHANGED"
    ADMIN_LOGGED_IN = "ADMIN_LOGGED_IN"
    ADMIN_REMOVED = "ADMIN_REMOVED"


@payload_schema.register(event_name=AdminEvent.ADMIN_CREATED)
class AdminCreatedEvent(AdminResponse):
    pass


@payload_schema.register(event_name=AdminEvent.ADMIN_UPDATED)
class AdminUpdatedEvent(AdminResponse):
    pass


@payload_schema.register(event_name=AdminEvent.ADMIN_PASSWORD_CHANGED)
class AdminPasswordChangedEvent(AdminResponse):
    pass


@payload_schema.register(event_name=AdminEvent.ADMIN_LOGGED_IN)
class AdminLoggedInEvent(AdminResponse):
    pass


@payload_schema.register(event_name=AdminEvent.ADMIN_REMOVED)
class AdminRemovedEvent(AdminResponse):
    pass
