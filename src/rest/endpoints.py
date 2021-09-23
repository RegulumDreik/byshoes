from uuid import UUID

from fastapi import APIRouter, Depends
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
from src.utils.utils import get_max_version

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
    last_items = collection.aggregate(
        [
            {'$match': {'version': {'$eq': max_version}}},
            {'$group': {'_id': {'$concat': ['$site', '$article']}}},
        ],
        allowDiskUse=True,
    )
    last_items = await last_items.to_list(None)
    last_items = {item['_id'] for item in last_items}
    depth = 0
    while True:
        depth += 1
        prev_items = collection.aggregate(
            [
                {'$match': {'version': {'$eq': max_version - depth}}},
                {'$group': {'_id': {'$concat': ['$site', '$article']}}},
            ],
            allowDiskUse=True,
        )
        prev_items = await prev_items.to_list(None)
        prev_items = {item['_id'] for item in prev_items}
        new_items = list(last_items - prev_items)
        if not (len(new_items) == 0 and depth < max_version):
            break
    new_items_ids = collection.aggregate(
        [
            {'$match': {'version': {'$eq': max_version}}},
            {'$group': {
                '_id': {'$concat': ['$site', '$article']},
                'id': {'$last': '$_id'},
            }},
            {'$match': {'_id': {'$in': new_items}}},
        ],
        allowDiskUse=True,
    )
    new_items_ids = await new_items_ids.to_list(None)
    new_items_ids = [item['id'] for item in new_items_ids]

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
    query_params: filter_params(ProductFilters) = Depends(),
) -> FilterStats:
    """Получение списка продуктов.

    Args:
        request: запрос
        query_params: параметры фильтров

    Returns:
        Список продуктов.

    """
    collection = request.app.mongodb['byshoes-collection']
    max_version = await get_max_version(
        collection,
    )
    filters = ProductFilters().apply(query_params)
    filters['version'] = {'$eq': max_version}
    query = collection.aggregate(
        [
            {'$match': filters},
            {'$unwind': {'path': '$specification.size'}},
            {'$group': {
                '_id': '$specification.size.size_type',
                'max_price': {'$max': '$price'},
                'min_price': {'$min': '$price'},
                'sizes': {'$addToSet': {
                    '$arrayElemAt': ['$specification.size.values', 0],
                }},
                'categories': {'$addToSet': '$category'},
                'color_types': {'$addToSet': '$specification.color'},
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
    return FilterStats(
        **(await query.next()),  # noqa: B305
        sex_types=[e.value for e in SexEnum],
        site_types=[e.value for e in SiteEnum],
    )


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
