from typing import Any, get_args, get_origin, get_type_hints
from urllib.parse import unquote_plus

from pydantic.fields import FieldInfo, ModelField


class FilterSet(object):
    """Набор доступных фильтров.

    Пример использования в tests/filters.py
    """

    class Meta(object):
        """Конфигурация набора фильтров."""

        model = None
        schema = None
        fields = None
        filter_backend = None

    @classmethod
    def get_default_filters(cls) -> list[dict[str, Any]]:
        """Сбор автогенеренных фильтров.

        Returns:
            набор доступных фильтров

        """
        fields = getattr(cls.Meta, 'fields', None) or []
        return [
            {
                'field': default_filter.field_info.extra.get(
                    'field',
                    name,
                ),
                'name': name,
                'description': name,
                'type': default_filter.type_,
                'operators': cls.Meta.filter_backend.OPERATORS.keys(),
            }
            for name, default_filter in cls.Meta.schema.__fields__.items()
            if isinstance(default_filter, ModelField) and name in fields
        ]

    @classmethod
    def _get_filter(cls, attr_name: str) -> dict[str, Any]:
        """Получает фильтр.

        Args:
            attr_name: название аттрибута

        Returns:
            фильтр
        """
        attr = getattr(cls, attr_name)
        if isinstance(attr, FieldInfo) and 'method' in attr.extra:
            return {
                'name': attr_name,
                'description': attr.description,
                'method': getattr(cls, attr.extra['method']),
                'type': get_type_hints(cls)[attr_name],
                'default': getattr(cls, attr_name).default,
            }

        elif isinstance(attr, FieldInfo) and 'fields' in attr.extra:
            return {
                'name': attr_name,
                'description': attr.description,
                'fields': getattr(cls, attr_name).extra['fields'],
                'type': get_type_hints(cls)[attr_name],
                'default': getattr(cls, attr_name).default,
            }

        elif isinstance(attr, FieldInfo):
            field_type = get_type_hints(cls)[attr_name]
            doc_type = str if get_origin(field_type) is list else field_type
            inner = get_args(field_type)[0] if get_args(field_type) else None
            return {
                'field': getattr(cls, attr_name).extra.get(
                    'field',
                    attr_name,
                ),
                'name': attr_name,
                'description': attr.description,
                'operators': getattr(cls, attr_name).extra.get(
                    'operators',
                    cls.Meta.filter_backend.OPERATORS.keys(),
                ),
                'type': doc_type,
                'inner_type': inner,
                'default': getattr(cls, attr_name).default,
            }

    @classmethod
    def _get_declared_filters(cls) -> list[dict[str, Any]]:
        """Сбор задекларированных фильтров.

        Returns:
            набор доступных фильтров

        """
        filters = []
        for attr_name in dir(cls):
            declared_filter = cls._get_filter(attr_name)
            if declared_filter:
                filters.append(declared_filter)
        return filters

    @classmethod
    def _find_filter(
        cls,
        filter_name: str,
        filters: list[dict[str, Any]],
    ) -> int:
        """Поиск фильтра по имени.

        Args:
            filter_name: имя фильтра
            filters: список фильтров

        Returns:
            позиция или None
        """
        for pos, filter_element in enumerate(filters):
            if filter_element['name'] == filter_name:
                return pos

    @classmethod
    def resolve(cls) -> list[dict[str, Any]]:
        """Формирует json объект нужный для фильтров.

        Returns:
            приведенные фильтра

        """
        filters = cls.get_default_filters()
        declared_filters = []
        for declared_filter in cls._get_declared_filters():
            exist_pos = cls._find_filter(declared_filter['name'], filters)
            if exist_pos is not None:
                filters[exist_pos] = declared_filter
            else:
                declared_filters.append(declared_filter)

        return filters + declared_filters

    def _crop_params(self, params: Any) -> dict[str, Any]:
        """Обрезка параметров.

        Args:
            params: класс с параметрами фильтров

        Returns:
            словарь с параметрами
        """
        filter_params = {}
        for param_key, param_value in params.__dict__.items():
            if isinstance(param_value, str):
                filter_params.update(
                    {param_key: unquote_plus(param_value).lower()},
                )
            elif param_value is not None:
                filter_params.update({param_key: param_value})
        return filter_params

    def apply(self, params: Any, query: Any = None) -> Any:
        """Применение фильтров.

        Args:
             params: параметры реквеста
             query: sql запрос

        Returns:
            запрос с примененными фильтрами

        """
        request_params = self._crop_params(params)

        return self.Meta.filter_backend(self).apply_filters(
            self.resolve(),
            request_params,
            query,
        )
