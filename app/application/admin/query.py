from sqlalchemy import select
from sqlalchemy.sql.functions import count

from app.apdapter.orm import session_scope
from app.application.admin.model import Admin
from app.application.admin.schema import AdminResponse
from app.common.code import Code
from app.common.exception import BadRequestException400
from app.common.schema import ListResult
from app.utils.pagination import get_pagination_list


async def get_admins(page: int, page_size: int, ordering: str | None = None) -> ListResult[AdminResponse]:
    initial_query = select(Admin).filter_by(removed_flag=False)
    count_query = select(count(Admin.id)).filter_by(removed_flag=False)

    return await get_pagination_list(
        initial_query=initial_query,
        count_query=count_query,
        schema_cls=AdminResponse,
        page=page,
        page_size=page_size,
        ordering=ordering,
    )


async def get_admin(admin_id: int) -> AdminResponse:
    with session_scope() as session:
        result = session.scalar(select(Admin).filter_by(id=admin_id).filter_by(removed_flag=False))
        if result is None:
            raise BadRequestException400(Code.UNKNOWN_ADMIN)
        return AdminResponse.model_validate(result)
