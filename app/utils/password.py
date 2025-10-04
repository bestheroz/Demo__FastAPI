import bcrypt


def _truncate_password_to_72_bytes(password: str) -> bytes:
    """bcrypt의 72바이트 제한에 맞게 비밀번호를 안전하게 자름.

    UTF-8 멀티바이트 문자가 중간에서 잘리지 않도록 처리합니다.
    """
    password_bytes = password.encode("utf-8")
    if len(password_bytes) <= 72:
        return password_bytes

    # 72바이트 이하로 안전하게 자르기 (멀티바이트 문자 중간에서 자르지 않음)
    truncated = password_bytes[:72]
    while len(truncated) > 0:
        try:
            # 유효한 UTF-8인지 확인
            truncated.decode("utf-8")
            return truncated
        except UnicodeDecodeError:
            # 마지막 바이트가 멀티바이트 문자의 중간이면 한 바이트씩 줄임
            truncated = truncated[:-1]

    return b""


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    """비밀번호 검증

    Args:
        plain_password: 평문 비밀번호
        hashed_password: 해시된 비밀번호 (None인 경우 False 반환)

    Returns:
        비밀번호 일치 여부
    """
    if hashed_password is None:
        return False

    password_bytes = _truncate_password_to_72_bytes(plain_password)
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def get_password_hash(password: str) -> str:
    """비밀번호 해싱"""
    password_bytes = _truncate_password_to_72_bytes(password)
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")
