from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.params import Param
from fastapi_pagination import Page
from starlette.requests import Request
from starlette.responses import JSONResponse

from filters import filter_params
from src.enums import SexEnum, SiteEnum
from src.models import (
    FilterStats,
    ProductModel,
    ProductModelList,
    ProductModelParse,
    ProductModelParseList,
)
from src.rest.filtering import ProductFilters
from src.rest.ordering import ProductOrdering
from src.utils.paginate import paginate
from src.utils.utils import get_max_version, get_newest_list

router = APIRouter(
    prefix='/api',
    tags=['byshoes'],
    responses={
        401: {'description': 'Need authentication'},
        403: {'description': 'Not enough privileges'},
        404: {'description': 'Item not found'},
        500: {'description': 'Something went wrong'},
        502: {'description': 'Technical work in progress'},
    },
)


@router.get(
    '/products',
    response_model=Page[ProductModel],
    responses={
        404: {'description': 'Item not found'},
    },
    description='Список продкутов только последнее спаршеное.',
)
async def get_product_list(
    request: Request,
    query_params: filter_params(ProductFilters) = Depends(),
    order: ProductOrdering = Depends(ProductOrdering),
) -> JSONResponse:
    """Получение списка продуктов.

    Args:
        request: запрос
        query_params: параметры фильтров
        order: параметры сортировки

    Returns:
        Список продуктов

    """
    max_version = await get_max_version(
        request.app.mongodb['byshoes-collection'],
    )
    filters = ProductFilters().apply(query_params)
    filters['version'] = {'$eq': max_version}
    sort_by, order_by = order.apply({})
    return await paginate(
        request.app.mongodb['byshoes-collection'],
        filters,
        ProductModelList,
        sort_by,
        order_by,
    )


@router.get(
    '/products/all',
    response_model=Page[ProductModelParse],
    response_model_by_alias=False,
    responses={
        404: {'description': 'Item not found'},
    },
    description='Список продкутов за все время.',
)
async def get_product_full_list(
    request: Request,
    query_params: filter_params(ProductFilters) = Depends(),
    order: ProductOrdering = Depends(ProductOrdering),
) -> JSONResponse:
    """Получение списка продуктов.

    Args:
        request: запрос
        query_params: параметры фильтров
        order: параметры сортировки

    Returns:
        Список продкутов

    """
    filters = ProductFilters().apply(query_params)
    sort_by, order_by = order.apply({})
    return await paginate(
        request.app.mongodb['byshoes-collection'],
        filters,
        ProductModelParseList,
        sort_by,
        order_by,
    )


@router.get(
    '/products/new',
    response_model=Page[ProductModelParse],
    response_model_by_alias=False,
    responses={
        404: {'description': 'Item not found'},
    },
    description='Список продкутов за все время.',
)
async def get_product_new_list(
    request: Request,
    query_params: filter_params(ProductFilters) = Depends(),
    order: ProductOrdering = Depends(ProductOrdering),
) -> JSONResponse:
    """Получение списка продуктов.

    Args:
        request: запрос
        query_params: параметры фильтров
        order: параметры сортировки

    Returns:
        Список продкутов

    """
    collection = request.app.mongodb['byshoes-collection']
    max_version = await get_max_version(collection)
    new_items_ids = await get_newest_list(collection)

    filters = ProductFilters().apply(query_params)
    filters['_id'] = {'$in': new_items_ids}
    filters['version'] = {'$eq': max_version}
    sort_by, order_by = order.apply({})
    return await paginate(
        collection,
        filters,
        ProductModelParseList,
        sort_by,
        order_by,
    )


@router.get(
    '/products/filter_stats',
    response_model=FilterStats,
    responses={
        404: {'description': 'Item not found'},
    },
    description='Информация о фильтрах.',
)
async def get_filter_stats(
    request: Request,
    is_new: Optional[bool] = None,
    query_params: filter_params(ProductFilters) = Depends(),
) -> FilterStats:
    """Получение списка продуктов.

    Args:
        request: запрос
        query_params: параметры фильтров
        is_new: фильтровать по новым.

    Returns:
        Список продуктов.

    """
    collection = request.app.mongodb['byshoes-collection']
    max_version = await get_max_version(
        collection,
    )
    filters = ProductFilters().apply(query_params)
    filters['version'] = {'$eq': max_version}
    if is_new is True:
        filters['_id'] = {'$in': await get_newest_list(collection)}
    elif is_new is False:
        filters['_id'] = {'$nin': await get_newest_list(collection)}
    query = collection.aggregate(
        [
            {'$match': filters},
            {'$unwind': {'path': '$specification.size'}},
            {'$group': {
                '_id': '$specification.size.size_type',
                'max_price': {'$max': '$price'},
                'min_price': {'$min': '$price'},
                'sizes': {'$addToSet': '$specification.size.values'},
                'categories': {'$addToSet': '$category'},
                'color_types': {'$addToSet': '$specification.color'},
                'sex_types': {'$addToSet': '$specification.sex'},
                'site_types': {'$addToSet': '$site'},
            }},
            {'$addFields': {
                'sizes': {
                    '$reduce': {
                        'input': '$sizes',
                        'initialValue': [],
                        'in': {'$setUnion': ['$$value', '$$this']},
                    },
                },
            }},
            {'$group': {
                '_id': None,
                'max_price': {'$max': '$max_price'},
                'min_price': {'$min': '$min_price'},
                'sizes': {'$addToSet': {
                    'size_type': '$_id',
                    'values': '$sizes',
                }},
                'categories': {'$addToSet': '$categories'},
                'color_types': {'$addToSet': '$color_types'},
                'sex_types': {'$addToSet': '$sex_types'},
                'site_types': {'$addToSet': '$site_types'},
            }},
            {'$addFields': {
                'categories': {
                    '$reduce': {
                        'input': '$categories',
                        'initialValue': [],
                        'in': {'$setUnion': ['$$value', '$$this']},
                    },
                },
                'color_types': {
                    '$reduce': {
                        'input': '$color_types',
                        'initialValue': [],
                        'in': {'$setUnion': ['$$value', '$$this']},
                    },
                },
                'sex_types': {
                    '$reduce': {
                        'input': '$sex_types',
                        'initialValue': [],
                        'in': {'$setUnion': ['$$value', '$$this']},
                    },
                },
                'site_types': {
                    '$reduce': {
                        'input': '$site_types',
                        'initialValue': [],
                        'in': {'$setUnion': ['$$value', '$$this']},
                    },
                },
            }},
            {'$addFields': {
                'categories': {
                    '$reduce': {
                        'input': '$categories',
                        'initialValue': [],
                        'in': {'$setUnion': ['$$value', '$$this']},
                    },
                },
                'color_types': {
                    '$reduce': {
                        'input': '$color_types',
                        'initialValue': [],
                        'in': {'$setUnion': ['$$value', '$$this']},
                    },
                },
            }},
        ],
        allowDiskUse=True,
    )
    return FilterStats(**(await query.next()))  # noqa: B305


@router.get(
    '/products/{product_id}',
    response_model=ProductModelParse,
    response_model_by_alias=False,
    responses={
        404: {'description': 'Item not found'},
    },
    description='Детальный вид.',
)
async def get_product_detail(
    request: Request,
    product_id: UUID,
) -> JSONResponse:
    """Получение списка продуктов.

    Args:
        request: запрос
        product_id: Идентификатор продукта

    Returns:
        Список продуктов.

    """
    return await request.app.mongodb['byshoes-collection'].find_one(
        {'_id': str(product_id)},
    )
