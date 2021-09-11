from enum import Enum, unique


@unique
class SexEnum(str, Enum):
    """Перечисление описывающие возможные варианты характеристик пола."""

    MALE = 'm'
    FEMALE = 'f'
    UNISEX = 'u'
