from pydantic import AwareDatetime, Field, SecretStr

from app.common.schema import IdCreatedUpdatedDto, Schema
from app.common.type import AuthorityEnum


class UserBase(Schema):
    login_id: str = Field(..., description="로그인 아이디")
    use_flag: bool = Field(True, description="사용 여부")
    name: str = Field(..., description="유저 이름(닉네임)")
    authorities: set[AuthorityEnum] = Field([], description="권한 목록")


class UserCreate(UserBase):
    password: SecretStr = Field(..., description="비밀번호")


class UserUpdate(UserBase):
    password: SecretStr | None = Field(None, description="비밀번호")


class UserChangePassword(Schema):
    new_password: SecretStr = Field(..., description="신규 비밀번호")
    old_password: SecretStr = Field(..., description="기존 비밀번호")


class UserResponse(IdCreatedUpdatedDto, UserBase):
    joined_at: AwareDatetime | None = Field(None, description="가입 일시")
    latest_active_at: AwareDatetime | None = Field(None, description="최근 활동 일시")


class UserSimple(Schema):
    id: int = Field(..., description="ID(KEY)")
    login_id: str = Field(..., description="로그인 아이디")
    name: str = Field(..., description="유저 이름(닉네임)")


class UserLogin(Schema):
    login_id: str = Field(..., description="로그인 아이디", examples=["developer"])
    password: SecretStr = Field(..., description="비밀번호", examples=["1"])
