from typing import Any


class FilterBackend(object):
    """Базовый класс для фильтр-бэкенда."""

    def __init__(self, filter_set: Any):
        """Конструктор базового класса бэкенда.

        Args:
            filter_set: набор фильтров
        """
        self.filter_set = filter_set
