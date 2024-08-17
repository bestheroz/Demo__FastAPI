from fastapi.responses import StreamingResponse
from pandas import DataFrame

from app.application.user.query import get_users_by_service_id
from app.utils.datetime_utils import format_to_kst_tz, now_iso8601_string
from app.utils.excel import make_excel_response


async def download_excel(
    service_id: int,
    filename: str | None = None,
    ids: set[int] | None = None,
) -> StreamingResponse:
    ids = ids or set()

    df = DataFrame(
        columns=[
            "key",
            "이름",
            "가입 플랫폼",
            "가입 수단",
            "이메일",
            "가입 일시",
            "상태",
            "신고 수",
            "마지막 로그인 일시",
        ],
    )
    data = get_users_by_service_id(service_id, 1, 999_999, "-id", ids=ids).items
    for index, item in enumerate(data):
        df.loc[index] = [
            item.id,
            item.name,
            item.join_platform.name,
            item.join_type.name,
            item.email_id,
            format_to_kst_tz(item.joined_at, "%Y-%m-%d %H:%M"),
            item.status.name,
            item.report.reported_cnt,
            format_to_kst_tz(item.latest_active_at, "%Y-%m-%d %H:%M"),
        ]

    return make_excel_response(
        df,
        col_length=len(df.columns),
        filename=(filename or f"약관목록__{now_iso8601_string()}.xlsx").replace(
            ".xlsx.xlsx",
            ".xlsx",
        ),
    )
