from typing import Optional

from fastapi import Query

from filters import OrderSet


class ProductOrdering(OrderSet):
    """Сортировка продуктов."""

    sort_by: Optional[str] = Query(
        'order',
        description='Имя поля по которому сортировать',
    )
    order_by: Optional[str] = Query(
        'desc',
        description='Направление сортировки',
    )
