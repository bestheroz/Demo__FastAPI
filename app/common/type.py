from enum import StrEnum


class EventType(StrEnum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class UserTypeEnum(StrEnum):
    ADMIN = "ADMIN"
    USER = "USER"


class AuthorityEnum(StrEnum):
    ADMIN_VIEW = "ADMIN_VIEW"
    ADMIN_EDIT = "ADMIN_EDIT"

    USER_VIEW = "USER_VIEW"
    USER_EDIT = "USER_EDIT"

    NOTICE_VIEW = "NOTICE_VIEW"
    NOTICE_EDIT = "NOTICE_EDIT"
