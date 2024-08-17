from enum import StrEnum


class UserJoinTypeEnum(StrEnum):
    EMAIL = "EMAIL"
    KAKAO = "KAKAO"
    NAVER = "NAVER"
    GOOGLE = "GOOGLE"
    APPLE = "APPLE"


class UserStatusEnum(StrEnum):
    ACTIVE = "ACTIVE"
    DISCIPLINED = "DISCIPLINED"
