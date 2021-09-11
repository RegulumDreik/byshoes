from typing import Any, Optional, Type

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi_pagination.api import resolve_params
from fastapi_pagination.bases import AbstractParams
from fastapi_pagination.default import Params
from pydantic import BaseModel

DESTINATION = {
    'desc': -1,
    'asc': 1,
}


async def paginate(
    query: Any,
    find_query: dict[str, Any],
    model: Type[BaseModel],
    sort_by: str,
    order_by: int,
    params: Optional[AbstractParams] = None,
) -> JSONResponse:
    """Метод подстраничного вывода данных для mongodb.

    Args:
        query: запрос в mongodb
        find_query: Параметр поиска
        model: Модель объекта который используется для отдачи.
        params: query параметры из url
        sort_by: объект сортировки
        order_by: направление сортировки

    Returns:
        Постраничный ответ

    """
    params: Params = resolve_params(params)

    queryset = query.aggregate(
        [
            {'$match': find_query},
            {'$sort': {sort_by: order_by}},
            {'$skip': (params.page - 1) * params.size},
        ],
        allowDiskUse=True,
    )

    items = await queryset.to_list(params.size)
    total = await query.count_documents(find_query)

    return JSONResponse({
        'items': jsonable_encoder(
            model.parse_obj(items).dict()['__root__'],
            by_alias=True,
        ),
        'total': total,
        'page': params.page,
        'size': params.size,
    })
