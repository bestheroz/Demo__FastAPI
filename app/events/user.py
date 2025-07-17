from enum import StrEnum

from fastapi_events.registry.payload_schema import registry as payload_schema

from app.schemas.user import UserResponse


class UserEvent(StrEnum):
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_PASSWORD_UPDATED = "USER_PASSWORD_UPDATED"
    USER_LOGGED_IN = "USER_LOGGED_IN"
    USER_REMOVED = "USER_REMOVED"


@payload_schema.register(event_name=UserEvent.USER_CREATED)
class UserCreated(UserResponse):
    pass


@payload_schema.register(event_name=UserEvent.USER_UPDATED)
class UserUpdated(UserResponse):
    pass


@payload_schema.register(event_name=UserEvent.USER_PASSWORD_UPDATED)
class UserPasswordUpdated(UserResponse):
    pass


@payload_schema.register(event_name=UserEvent.USER_LOGGED_IN)
class UserLoggedIn(UserResponse):
    pass


@payload_schema.register(event_name=UserEvent.USER_REMOVED)
class UserRemoved(UserResponse):
    pass
