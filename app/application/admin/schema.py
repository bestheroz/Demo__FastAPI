from pydantic import AwareDatetime, EmailStr, Field, SecretStr

from app.common.schema import Schema, IdCreatedUpdatedDto
from app.common.type import AuthorityEnum


class AdminBase(Schema):
    login_id: str = Field(..., description="로그인 아이디")
    name: str = Field(..., description="관리자 계정 이름")
    use_flag: bool = Field(True, description="사용 여부")
    email_id: EmailStr = Field(..., description="이메일")
    manager_flag: bool = Field(..., description="매니저 여부(모든 권한 소유)")
    authorities: set[AuthorityEnum] = Field([], description="권한 목록")


class AdminResponse(IdCreatedUpdatedDto, AdminBase):
    id: int = Field(..., description="관리자 계정 ID")
    joined_at: AwareDatetime | None = Field(None, description="가입 일시")
    latest_active_at: AwareDatetime | None = Field(None, description="최근 활동 일시")


class AdminUpdate(AdminBase):
    pass


class AdminLogin(Schema):
    login_id: str = Field(..., description="로그인 아이디")
    password: SecretStr = Field(..., description="비밀번호")


class AdminChangePassword(Schema):
    password: SecretStr = Field(..., description="비밀번호")
    new_password: SecretStr = Field(..., description="새 비밀번호")
