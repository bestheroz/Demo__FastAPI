from pydantic import AwareDatetime, EmailStr, Field

from app.application.user.discipline.schema import UserDisciplineResponse
from app.application.user.history.schema import UserHistoryBase
from app.application.user.type import UserJoinTypeEnum, UserStatusEnum
from app.application.user.zip_service.schema import (
    UserZipServiceCreate,
    UserZipServiceResponse,
)
from app.common.schema import Schema, IdCreatedUpdatedDto
from app.utils.datetime_utils import utcnow


class UserBase(Schema):
    login_id: str = Field(..., description="로그인 아이디")
    use_flag: bool = Field(True, description="사용 여부")
    name: str = Field(..., description="유저 이름(닉네임)")
    image_url: str | None = Field(None, description="프로필 이미지 URL")
    email_id: EmailStr = Field(..., description="이메일")


class UserReportResponse(Schema):
    total_report_count: int = Field(0, description="전체 신고 횟수(게시글, 유저)")
    reported_board_cnt: int = Field(0, description="신고 받은 게시글 수")
    reported_cnt: int = Field(0, description="신고 받은 수")


class UserAdditionalInfoCreate(UserZipServiceCreate):
    pass


class UserAdditionalInfoResponse(UserZipServiceResponse):
    board_cnt: int | None = Field(0, description="게시글 수")


class UserResponse(IdCreatedUpdatedDto, UserBase):
    status: UserStatusEnum = Field(..., description="상태")
    join_platform: PlatformEnum = Field(..., description="가입 플랫폼")
    platform_version: str | None = Field(None, description="플랫폼 버전")
    join_type: UserJoinTypeEnum = Field(..., description="가입 수단")
    joined_flag: bool = Field(False, description="가입 여부")
    joined_at: AwareDatetime | None = Field(None, description="가입 일시")
    latest_active_at: AwareDatetime | None = Field(None, description="최근 활동 일시")
    report: UserReportResponse = Field(..., description="신고 정보")
    discipline: UserDisciplineResponse = Field(..., description="징계 정보")
    removed_flag: bool = Field(False, description="탈퇴 여부")
    removed_at: AwareDatetime | None = Field(None, description="탈퇴 일시")
    removed_reason: str | None = Field(None, description="탈퇴 사유")
    archive_expiration_at: AwareDatetime | None = Field(
        None, description="데이터 보관 만료 일시"
    )
    history_description: str | None = Field(None, description="히스토리 저장용")


class UserDetailResponse(UserResponse):
    platform_version: str | None = Field(None, description="플랫폼 버전")
    additional_info: UserAdditionalInfoResponse = Field(..., description="추가 정보")
    history: list[UserHistoryBase] = Field(..., description="관리자 업데이트 히스토리")


class UserEvent(UserResponse):
    service: ServiceResponse = Field(..., description="서비스 정보")
    verify_token: str = Field(..., description="인증 토큰")


class UserRecovery(Schema):
    reason: str | None = Field(None, description="사유")


class UserSimple(Schema):
    id: int = Field(..., description="ID(KEY)")
    name: str = Field(..., description="유저 이름(닉네임)")
    image_url: str | None = Field(None, description="프로필 이미지 URL")
    email_id: EmailStr = Field(..., description="이메일")


class UserMarketingTermsBase(Schema):
    email_agree_flag: bool = Field(False, description="이메일 수신 동의 여부")
    sms_agree_flag: bool = Field(False, description="SMS 수신 동의 여부")
    call_agree_flag: bool = Field(False, description="전화 수신 동의 여부")
    post_agree_flag: bool = Field(False, description="우편 수신 동의 여부")


class UserMarketingTermsResponse(UserMarketingTermsBase):
    email_agree_at: AwareDatetime | None = Field(
        None, description="이메일 수신 동의 일시"
    )
    sms_agree_at: AwareDatetime | None = Field(None, description="SMS 수신 동의 일시")
    call_agree_at: AwareDatetime | None = Field(None, description="전화 수신 동의 일시")
    post_agree_at: AwareDatetime | None = Field(None, description="우편 수신 동의 일시")


class UserMarketingTermsCreate(UserMarketingTermsBase):
    def to_response(
        self,
    ) -> UserMarketingTermsResponse:
        now = utcnow()
        return UserMarketingTermsResponse(
            email_agree_flag=self.email_agree_flag,
            email_agree_at=now if self.email_agree_flag else None,
            sms_agree_flag=self.sms_agree_flag,
            sms_agree_at=now if self.sms_agree_flag else None,
            call_agree_flag=self.call_agree_flag,
            call_agree_at=now if self.call_agree_flag else None,
            post_agree_flag=self.post_agree_flag,
            post_agree_at=now if self.post_agree_flag else None,
        )
