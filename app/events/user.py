from fastapi_events.registry.payload_schema import registry as payload_schema

from app.schemas.user import UserResponse


@payload_schema.register(event_name="UserCreatedEvent")
class UserCreated(UserResponse):
    pass


@payload_schema.register(event_name="UserUpdatedEvent")
class UserUpdated(UserResponse):
    pass


@payload_schema.register(event_name="UserPasswordUpdatedEvent")
class UserPasswordUpdated(UserResponse):
    pass


@payload_schema.register(event_name="UserLoggedInEvent")
class UserLoggedIn(UserResponse):
    pass


@payload_schema.register(event_name="UserRemovedEvent")
class UserRemoved(UserResponse):
    pass
