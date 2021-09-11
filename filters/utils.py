from dataclasses import field, make_dataclass
from typing import Any, Type

from fastapi import Query

from filters.filterset import FilterSet


def filter_params(filter_set: Type[FilterSet]) -> Any:
    """Генерация документации на параметры фильтров.

    Args:
        filter_set: класс, унаследованный от FilterSet

    Returns:
        датакласс с аттрибутами-параметрами реквеста
    """
    docs = filter_set.resolve()
    attrs = []
    for doc in docs:
        if 'operators' in doc:
            for op in doc['operators']:
                attrs.append(
                    (
                        '{0}_{1}'.format(doc['name'], op),
                        doc['type'],
                        field(
                            default=Query(
                                doc.get('default'),
                                description='Фильтр {0}_{1}'.format(
                                    doc['description'],
                                    op,
                                ),
                            ),
                        ),
                    ),
                )
        else:
            attrs.append(
                (
                    doc['name'],
                    doc['type'],
                    field(
                        default=Query(
                            doc.get('default'),
                            description='Фильтр {0}'.format(
                                doc['description'],
                            ),
                        ),
                    ),
                ),
            )

    return make_dataclass('{0}_docs'.format(filter_set.__name__), attrs)
