from pydantic import AwareDatetime, Field

from app.common.schema import Schema, IdCreatedUpdatedDto


class UserBase(Schema):
    login_id: str = Field(..., description="로그인 아이디")
    use_flag: bool = Field(True, description="사용 여부")
    name: str = Field(..., description="유저 이름(닉네임)")


class UserResponse(IdCreatedUpdatedDto, UserBase):
    joined_at: AwareDatetime | None = Field(None, description="가입 일시")
    latest_active_at: AwareDatetime | None = Field(None, description="최근 활동 일시")
    removed_flag: bool = Field(False, description="탈퇴 여부")
    removed_at: AwareDatetime | None = Field(None, description="탈퇴 일시")
    removed_reason: str | None = Field(None, description="탈퇴 사유")


class UserSimple(Schema):
    id: int = Field(..., description="ID(KEY)")
    login_id: str = Field(..., description="로그인 아이디")
    name: str = Field(..., description="유저 이름(닉네임)")
