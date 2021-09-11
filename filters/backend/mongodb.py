import re
from typing import Any

from filters.backend.base_backend import FilterBackend


class MongodbBackend(FilterBackend):
    """Бэкенд фильтра для mongodb."""

    OPERATORS = {
        'eq': '$eq',
        'lt': '$lt',
        'gt': '$gt',
        'le': '$lte',
        'ge': '$gte',
        'ne': '$ne',
        'in': '$in',
        'not_in': '$nin',
    }

    def _get_inner_field_type(self, field: str) -> Any:
        """Возвращает самый внутренний тип.

        Args:
            field: название поля

        Returns:
            тип самого вложенного поля
        """
        inner = self.filter_set.Meta.schema
        for item in field.split('.'):
            try:
                inner = inner.__fields__[item].type_
            except (AttributeError, KeyError):
                break
        return inner

    def _fill_mongodb_condition(
        self,
        field: str,
        value: Any,
    ) -> dict[str, Any]:
        """Готовит условия для фильтра с несколькими полями.

        Args:
            field: название поля
            value: значение

        Returns:
            Условие
        """
        if self._get_inner_field_type(field) is int:
            try:
                return {field: int(value)}
            except ValueError:
                return {field: value}
        pattern = re.compile(re.escape(value), re.IGNORECASE)
        return {field: {'$regex': pattern}}

    def _prepare_mongo_condition(
        self,
        model_filter: dict[str, Any],
        operator: str,
        value: Any,
    ) -> dict[str, Any]:
        """Подготовка условия для запроса к mongodb.

        Args:
            model_filter: фильтр
            operator: оператор
            value: значение фильтра

        Returns:
            запрос с примененным фильтром
        """
        operators = model_filter['operators']
        if model_filter.get('inner_type') and operator in operators:
            return {
                model_filter['field']: {
                    self.OPERATORS[operator]:
                        [
                            model_filter['inner_type'](val.strip())
                            for val in value.split(',')
                    ],
                },
            }
        if operator in operators:
            return {
                model_filter['field']: {
                    self.OPERATORS[operator]: value,
                },
            }

    def _get_mongo_filter(
        self,
        model_filter: dict[str, Any],
        parameter: str,
        value: Any,
    ) -> dict[str, Any]:
        """Получение mongo фильтра.

        Args:
            model_filter: фильтр
            parameter: параметр реквеста
            value: значение параметра реквеста

        Returns:
            запрос с примененным фильтром

        """
        if 'method' in model_filter:
            return model_filter['method'](self, parameter, value)

        if 'fields' in model_filter:
            return {'$or': [
                self._fill_mongodb_condition(field, value)
                for field, _ in model_filter['fields'].items()
            ]}

        operator = parameter.replace('{0}_'.format(model_filter['name']), '')
        if operator in model_filter['operators']:
            return self._prepare_mongo_condition(
                model_filter,
                operator,
                value,
            )

        return {}

    def _apply_mongo_filter(
        self,
        model_filter: dict[str, Any],
        parameter: str,
        value: Any,
        query: dict[str, Any],
    ) -> None:
        """Применение монго фильтра.

        Args:
            model_filter: фильтр
            parameter: параметр
            value: значение
            query: запрос

        """
        field_filter = self._get_mongo_filter(model_filter, parameter, value)
        if model_filter.get('field') in query:
            query[model_filter['field']].update(
                field_filter[model_filter['field']],
            )
        else:
            query.update(field_filter)

    def apply_filters(
        self,
        filters: list[dict[str, Any]],
        params: Any,
        query: Any = None,
    ):
        """Применение фильтров для mongo.

        Args:
            filters: фильтры
            params: параметры реквеста
            query: запрос (для совместимости)

        Returns:
            запрос с примененными фильтрами

        """
        query = {}
        for model_filter in filters:
            for parameter, value in params.items():
                if parameter.startswith(model_filter['name']):
                    self._apply_mongo_filter(
                        model_filter,
                        parameter,
                        value,
                        query,
                    )

        return query
