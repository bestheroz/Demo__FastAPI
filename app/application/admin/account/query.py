from sqlalchemy import select

from app.apdapter.orm import session_scope
from app.application.admin.account.model import AdminAccount
from app.application.admin.account.schema import AdminAccountResponse
from app.common.code import Code
from app.common.exception import RequestException400


def get_admin_account(admin_account_id: int) -> AdminAccountResponse:
    with session_scope() as session:
        result = session.scalar(select(AdminAccount).filter_by(id=admin_account_id))
        if result is None:
            raise RequestException400(Code.UNKNOWN_ACCOUNT)
        return AdminAccountResponse.model_validate(result)
