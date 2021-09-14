from typing import Literal

from pydantic import Field

from filters import FilterSet, MongodbBackend
from src.enums import SexEnum
from src.models import ProductModel


class ProductFilters(FilterSet):
    """Фильтр для продукта."""

    search: str = Field(
        fields={
            'title': 'contains',
            'article': 'contains',
        },
        description='по названию',
    )
    article: str = Field(
        field='article',
        operators=['eq'],
        description='по артикулу',
    )
    price: int = Field(
        operators=['ge', 'le'],
        description='по цене',
    )
    sex_list: list[SexEnum] = Field(
        field='specification.sex',
        operators=['in', 'not_in'],
        description='по полу',
    )
    sex: SexEnum = Field(
        field='specification.sex',
        operators=['eq', 'ne'],
        description='по полу',
    )
    color_list: list[str] = Field(
        field='specification.color',
        operators=['in', 'not_in'],
        description='по цветам',
    )
    color: str = Field(
        field='specification.color',
        operators=['eq', 'ne'],
        description='по цвету',
    )
    category_id_list: list[str] = Field(
        field='category.id',
        operators=['in', 'not_in'],
        description='по категории',
    )
    category_id: str = Field(
        field='category.id',
        operators=['eq', 'ne'],
        description='по категории',
    )
    category_search: str = Field(
        fields={
            'category.id': 'contains',
            'category.name': 'contains',
        },
        description='по категории',
    )
    size_type: str = Field(
        field='specification.size.size_type',
        operators=['eq'],
        description='по типу размера',
    )
    size_list: list[float] = Field(
        field='specification.size.values',
        operators=['in', 'not_in'],
        description='по размеру',
    )
    size_value: float = Field(
        field='specification.size.values',
        operators=['eq', 'ne'],
        description='по размеру',
    )
    site: Literal['multisports', 'allstars'] = Field(
        field='site',
        operators=['eq'],
        description='по сайту с которого спарсили',
    )

    class Meta(object):
        """Конфигурация набора фильтров."""

        schema = ProductModel
        filter_backend = MongodbBackend
