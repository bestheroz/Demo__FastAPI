from pydantic import AwareDatetime, Field

from app.common.schema import IdCreatedUpdatedDto, Schema


class UserBase(Schema):
    login_id: str = Field(..., description="로그인 아이디")
    use_flag: bool = Field(True, description="사용 여부")
    name: str = Field(..., description="유저 이름(닉네임)")


class UserCreate(UserBase):
    password: str = Field(..., description="비밀번호")


class UserUpdate(UserBase):
    password: str | None = Field(None, description="비밀번호")


class UserUpdatePassword(Schema):
    new_password: str = Field(..., description="신규 비밀번호")
    old_password: str = Field(..., description="기존 비밀번호")


class UserResponse(IdCreatedUpdatedDto, UserBase):
    joined_at: AwareDatetime | None = Field(None, description="가입 일시")
    latest_active_at: AwareDatetime | None = Field(None, description="최근 활동 일시")


class UserSimple(Schema):
    id: int = Field(..., description="ID(KEY)")
    login_id: str = Field(..., description="로그인 아이디")
    name: str = Field(..., description="유저 이름(닉네임)")
