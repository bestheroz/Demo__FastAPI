from pydantic import AwareDatetime, Field, SecretStr

from app.schemas.base import IdCreatedUpdatedDto, Pagination, Schema
from app.types.base import AuthorityEnum


class AdminBase(Schema):
    login_id: str = Field(..., description="로그인 아이디")
    name: str = Field(..., description="관리자 이름")
    use_flag: bool = Field(True, description="사용 여부")
    manager_flag: bool = Field(..., description="매니저 여부(모든 권한 소유)")
    authorities: set[AuthorityEnum] = Field(default_factory=set, description="권한 목록")


class AdminCreate(AdminBase):
    password: SecretStr = Field(..., description="비밀번호")


class AdminUpdate(AdminBase):
    password: SecretStr | None = Field(None, description="비밀번호")


class AdminResponse(IdCreatedUpdatedDto, AdminBase):
    joined_at: AwareDatetime | None = Field(None, description="가입 일시")
    latest_active_at: AwareDatetime | None = Field(None, description="최근 활동 일시")
    change_password_at: AwareDatetime | None = Field(None, description="비밀번호 변경 일시")


class AdminLogin(Schema):
    login_id: str = Field(..., description="로그인 아이디", examples=["developer"])
    password: SecretStr = Field(
        ...,
        description="비밀번호",
        examples=[
            "4dff4ea340f0a823f15d3f4f01ab62eae0e5da579ccb851f8db9dfe84c58b2b37b89903a740e1ee172da793a6e79d560e5f7f9bd058a12a280433ed6fa46510a"
        ],
    )


class AdminChangePassword(Schema):
    old_password: SecretStr = Field(..., description="비밀번호")
    new_password: SecretStr = Field(..., description="새 비밀번호")


class AdminListRequest(Pagination):
    id: int | None = Field(None, description="ID(KEY)")
    login_id: str | None = Field(None, description="로그인 아이디")
    name: str | None = Field(None, description="관리자 이름")
    use_flag: bool | None = Field(None, description="사용 여부")
    manager_flag: bool | None = Field(None, description="매니저 여부")
