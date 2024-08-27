from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, AwareDatetime, Field
from pydantic.alias_generators import to_camel

from app.common.type import UserTypeEnum, AuthorityEnum


class Schema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


T = TypeVar("T")


class ListApiResult(Schema, Generic[T]):
    page: int
    page_size: int
    total: int
    items: list[T]


class AvailableFlag(Schema):
    available_flag: bool


class TokenBase(Schema):
    access_token: str
    refresh_token: str


class DisplayOrder(Schema):
    id: int
    display_order: int


class UserSimpleDto(Schema):
    id: int = Field(..., description="ID(KEY)")
    type: UserTypeEnum = Field(..., description="관리자 or 유저")
    login_id: str = Field(..., description="관리자 ID or 유저 계정 ID")
    name: str = Field(..., description="관리자 이름 or 유저 이름")


class CreatedDto(Schema):
    created_at: AwareDatetime = Field(..., description="생성일시")
    created_by: UserSimpleDto = Field(..., description="생성자")


class IdCreatedDto(CreatedDto):
    id: int = Field(..., description="ID(KEY)")


class UpdatedDto(Schema):
    updated_at: AwareDatetime = Field(..., description="수정일시")
    updated_by: UserSimpleDto = Field(..., description="수정자")


class IdUpdatedDto(UpdatedDto):
    id: int = Field(..., description="ID(KEY)")


class CreatedUpdateDto(CreatedDto, UpdatedDto):
    pass


class IdCreatedUpdatedDto(CreatedUpdateDto):
    id: int = Field(..., description="ID(KEY)")


class RefreshTokenClaims(Schema):
    id: int = Field(..., description="관리자 ID")


class AccessTokenClaims(Schema):
    id: int = Field(..., description="관리자 ID")
    login_id: str = Field(..., description="로그인 아이디")
    name: str = Field(..., description="관리자 이름")
    manager_flag: bool = Field(..., description="매니저 여부(모든 권한 소유)")
    authorities: list[AuthorityEnum] = Field([], description="권한 목록")
