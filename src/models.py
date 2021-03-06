import uuid
from datetime import datetime
from typing import Any, Optional

import pytz
from camel_snake_kebab import snake_case
from pydantic import BaseModel, Field, HttpUrl, root_validator, validator

from src.enums import SexEnum, SiteEnum


class Size(BaseModel):
    """Модель описывающая размеры определённого класса."""

    size_type: str = Field(description='Тип размера, US, RU, CM.')
    values: list[float] = Field(description='Список размеров данного типа.')


class Specification(BaseModel):
    """Модель описывающая подробности модели."""

    size: list[Size] = Field(description='Список размеров по типам.')
    color: list[str] = Field(
        description='Цвет модели.',
        default=['неизвестно'],
    )
    sex: SexEnum = Field(description='Пол модели.')

    @validator('color', pre=True, each_item=True)
    @classmethod
    def null_remove(cls, value: Optional[str]) -> str:
        """Преобразования нулевого цвета в неизвестный.

        Args:
            value: Значение для валидации.

        Returns:
            Провалидированное значение.
        """
        if value is None:
            return 'неизвестно'
        if value.lower() == 'array':
            return 'неизвестно'
        return value.lower()


class Category(BaseModel):
    """Модель описывающая отдельную категорию."""

    id: str = Field(description='Идентификатор категории.')
    name: str = Field(description='Читаемое название категории.')

    @root_validator
    @classmethod
    def validate_class(cls, values):
        """Метод сокращения не нужных категорий.

        Args:
            values: Значения

        Returns:
            Провалидированное значения
        """
        if snake_case(values['id']) == 'krossovki_vysokie':
            return {'id': 'krossovki', 'name': 'кроссовки'}
        if snake_case(values['id']) == 'nike':
            return {'id': 'krossovki', 'name': 'кроссовки'}
        return values

    @validator('id')
    @classmethod
    def validator_id(cls, value):
        """Метод для нормализации идентификатора модели.

        Args:
            value: значение для валидации

        Returns:
            провалидированное значение
        """
        return snake_case(value)

    @validator('name')
    @classmethod
    def validator_name(cls, value):
        """Метод для нормализации идентификатора модели.

        Args:
            value: значение для валидации

        Returns:
            провалидированное значение
        """
        return value.lower()

    class Config:
        """Класс конфигурации модели."""

        frozen = True


class ProductModelParse(BaseModel):
    """Модель обуви.

    Используется для записи в базу данных.
    """

    id: str = Field(
        description='Идентификатор модели.',
        default_factory=uuid.uuid4,
        alias='_id',
    )
    title: str = Field(description='Идентификатор категории.')
    images: list[HttpUrl] = Field(description='Список картинок модели.')
    link: HttpUrl = Field(description='Адрес страницы с которой спарсили.')
    price: float = Field(description='Цена.')
    discounted_price: Optional[float] = Field(description='Цена до скидки.')
    category: list[Category] = Field(description='Список категорий модели.')
    specification: Specification = Field(description='Спецификация модели.')
    site: SiteEnum = Field(
        description='Сайт с которого спарсили.',
    )
    article: Optional[str] = Field(description='Артикул модели.')
    parsed: datetime = Field(
        description='Дата когда спарсили.',
        default_factory=lambda: datetime.now(pytz.utc),
    )
    version: Optional[int] = Field(
        description='Запуск парсера для получения данного объекта.',
    )


class ProductModel(ProductModelParse):
    """Модель обуви.

    Используется для отображения из view.
    """

    id: str = Field(
        description='Идентификатор модели.',
        default_factory=uuid.uuid4,
    )


class FilterStats(BaseModel):
    """Информация о доступных значениях в фильтрах."""

    categories: list[Category] = Field(
        description='Список доступных категорий.',
    )
    sizes: list[Size] = Field(description='Список доступных размеров.')
    sex_types: list[str] = Field(description='Список доступных полов.')
    site_types: list[str] = Field(description='Список доступных сайтов.')
    color_types: list[str] = Field(description='Список доступных цветов.')
    min_price: float = Field(description='Минимальная цена.')
    max_price: float = Field(description='Максимальная цена.')

    @validator('sizes', pre=True)
    @classmethod
    def null_remove(cls, values: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Преобразования нулевого цвета в неизвестный.

        Args:
            values: Значение для валидации.

        Returns:
            Провалидированное значение.
        """
        out = []
        for size in values:
            if size['size_type'] is not None:
                out.append(size)
        return out


class ProductModelList(BaseModel):
    """Список продуктов.

    Требуется для корректной работы постраничного запроса
    """

    __root__: list[ProductModel]


class ProductModelParseList(BaseModel):
    """Список продуктов.

    Требуется для корректной работы постраничного запроса
    """

    __root__: list[ProductModelParse]
