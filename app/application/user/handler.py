from asyncio import run

from sqlalchemy.orm import Session

from app.application.user.history.model import UserHistory
from app.application.user.schema import UserEvent, UserResponse
from app.common.event import Event
from app.config.config import get_settings
from app.utils.email import send_email

settings = get_settings()


def send_email_for_user_password_reset(event: Event[UserEvent]):
    if settings.deployment_environment == "test":
        return
    data = event.data
    run(
        send_email(
            recipients={
                data.login_id,
            },
            subject=f"[{data.service.name}]유저의 비밀번호가 초기화 되었습니다.",
            body_html=f"""
            <p>유저의 비밀번호가 초기화 되었습니다.</p>
            <p>로그인 아이디: {data.login_id}</p>
            <p>인증 토큰: {data.verify_token}</p>
            <p>인증 url: {settings.zip_service_web_host}resetPassword?token={data.verify_token}&id={data.id}</p>
            """,
        )
    )


def append_user_history(event: Event[UserResponse], session: Session) -> None:
    data = event.data
    if data.history_description is not None:
        session.add(
            UserHistory(
                user_id=data.id,
                description=data.history_description,
                created_at=data.updated_at,
                created_by_id=data.updated_by.id,
                created_object_type=data.updated_by.type,
            )
        )
