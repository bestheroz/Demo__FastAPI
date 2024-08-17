from enum import StrEnum


class NoticeStatusEnum(StrEnum):
    ACTIVE = "ACTIVE"
    REMOVED_BY_ADMIN = "REMOVED_BY_ADMIN"
    REMOVED_BY_MEMBER = "REMOVED_BY_MEMBER"
