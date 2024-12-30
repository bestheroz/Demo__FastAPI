from enum import StrEnum


class Code(StrEnum):
    UNKNOWN_SYSTEM_ERROR = "알 수 없는 시스템 오류"
    UNKNOWN_AUTHENTICATION = "알 수 없는 인증 정보"
    UNKNOWN_AUTHORITY = "알 수 없는 권한"
    UNKNOWN_ADMIN = "알 수 없는 관리자"
    UNKNOWN_USER = "알 수 없는 유저"
    UNKNOWN_NOTICE = "알 수 없는 공지"
    INVALID_ACCESS = "잘못된 접근"
    INVALID_PASSWORD = "잘못된 비밀번호"
    INVALID_PARAMETER = "잘못된 요청 값"
    CANNOT_UPDATE_YOURSELF = "자신의 정보는 변경 불가능"
    CANNOT_REMOVE_YOURSELF = "자신의 정보는 삭제 불가능"
    ALREADY_JOINED_ACCOUNT = "이미 가입된 계정"
    UNJOINED_ACCOUNT = "가입되지 않은 계정"
    CHANGE_TO_SAME_PASSWORD = "이전과 동일한 비밀번호로 변경 불가능"
    EXPIRED_TOKEN = "만료된 토큰 정보"
    CANNOT_CHANGE_OTHERS_PASSWORD = "다른 사용자의 비밀번호 변경 불가능"
