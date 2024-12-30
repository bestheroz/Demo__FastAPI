from pydantic.alias_generators import to_snake
from sqlalchemy import Select, desc
from sqlalchemy.orm import Session

from app.schemas.base import ListResult


async def get_pagination_list(
    schema_cls,
    session: Session,
    page: int,
    page_size: int,
    initial_query: Select,
    count_query: Select,
    ordering: str | None = None,
) -> ListResult:
    async def _get_pagination_list():
        query = initial_query

        if ordering:
            for ordering_condition in ordering.split(","):
                if ordering_condition.startswith("-"):
                    camel_str = to_snake(ordering_condition[1:])
                    query = query.order_by(desc(camel_str))
                else:
                    camel_str = to_snake(ordering_condition)
                    query = query.order_by(camel_str)

        results = (session.scalars(query.limit(page_size).offset((page - 1) * page_size))).all()
        _obj_data_list = [schema_cls.model_validate(model_obj) for model_obj in results]
        return _obj_data_list

    obj_data_list = await _get_pagination_list()
    total_obj = session.scalar(count_query)

    return ListResult[schema_cls](items=obj_data_list, total=total_obj or 0, page=page, page_size=page_size)
