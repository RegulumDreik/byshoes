from motor.motor_asyncio import AsyncIOMotorCollection


async def get_max_version(db: AsyncIOMotorCollection) -> int:
    """Получает из базы максимальную версию объектов.

    Args:
        db: Инстанс бд

    Returns:
        максимальная версия в базе данных

    """
    query = db.aggregate(
        [
            {
                '$group': {
                    '_id': None,
                    'parse_version': {'$max': '$version'},
                },
            },
        ],
        allowDiskUse=True,
    )
    parse_version = await query.to_list(None)
    parse_version = parse_version[0]['parse_version']
    return 0 if parse_version is None else parse_version