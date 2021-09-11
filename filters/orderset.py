from typing import Any, Optional

from fastapi import Query
from pydantic import BaseModel


class OrderSet(BaseModel):
    """Базовая сортирока."""

    class Meta(object):
        """Конфигурация сортировки."""

        model = None

    sort_by: Optional[str] = Query(
        None,
        description='Наименование поля сортировки',
    )
    order_by: Optional[str] = Query(
        'asc',
        description='Направление сортировки',
    )

    def apply(self, query: Any) -> Any:
        """Применение фильтров.

        Args:
             query: sql запрос

        Returns:
            запрос с примененными фильтрами к нему

        """
        params = self.dict(exclude_unset=True, exclude_none=True)
        if not self.Meta.model:
            order = {'desc': -1, 'asc': 1}[params.get('order_by', 'asc')]
            return params.get('sort_by'), order
