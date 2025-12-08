from pydantic.alias_generators import to_snake
from sqlalchemy import Select, text
from sqlalchemy.orm import Session

from app.schemas.base import ListResult


def get_pagination_list(
    schema_cls,
    session: Session,
    page: int,
    page_size: int,
    initial_query: Select,
    count_query: Select,
    ordering: str | None = None,
) -> ListResult:
    query = initial_query

    if ordering:
        order_clauses = []
        for ordering_condition in ordering.split(","):
            if ordering_condition.startswith("-"):
                column_name = to_snake(ordering_condition[1:])
                order_clauses.append(text(f"{column_name} DESC"))
            else:
                column_name = to_snake(ordering_condition)
                order_clauses.append(text(f"{column_name} ASC"))
        query = query.order_by(*order_clauses)

    results = session.scalars(query.limit(page_size).offset((page - 1) * page_size)).all()
    obj_data_list = [schema_cls.model_validate(model_obj) for model_obj in results]
    total_obj = session.scalar(count_query)

    return ListResult[schema_cls](items=obj_data_list, total=total_obj or 0, page=page, page_size=page_size)
