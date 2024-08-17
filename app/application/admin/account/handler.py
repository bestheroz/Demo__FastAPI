from asyncio import run

from app.application.admin.schema import AdminAccountCreateEvent
from app.common.event import Event
from app.config.config import get_settings
from app.utils.datetime_utils import to_iso8601_string
from app.utils.email import send_email

settings = get_settings()


def send_email_for_admin_account_created(event: Event[AdminAccountCreateEvent]):
    if settings.deployment_environment == "test":
        return
    data = event.data
    run(
        send_email(
            recipients={
                data.login_id,
            },
            subject="[NO-IT]관리자 계정이 생성되었습니다.",
            body_html=f"""
            <p>관리자 계정이 생성되었습니다.</p>
            <p>로그인 아이디: {data.login_id}</p>
            <p>계정 생성 일시: {to_iso8601_string(data.created_at)}</p>
            <p>인증 토큰: {data.verify_token}</p>
            <p>인증 url: {settings.noit_web_host}verifyJoin?token={data.verify_token}&id={data.id}
            &loginId={data.login_id}</p>
            """,
        )
    )
