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
    if len(parse_version) == 0:
        return 0
    parse_version = parse_version[0]['parse_version']
    return 0 if parse_version is None else parse_version


async def get_newest_list(db: AsyncIOMotorCollection) -> list[str]:
    """Получает список новинок.

    Args:
        db: База данных

    Returns:
        Список новинок.
    """
    max_version = await get_max_version(db)
    last_items = db.aggregate(
        [
            {'$match': {'version': {'$eq': max_version}}},
            {'$group': {'_id': {'$concat': ['$site', '$article']}}},
        ],
        allowDiskUse=True,
    )
    last_items = await last_items.to_list(None)
    last_items = {item['_id'] for item in last_items}
    depth = 0
    while True:
        depth += 1
        prev_items = db.aggregate(
            [
                {'$match': {'version': {'$eq': max_version - depth}}},
                {'$group': {'_id': {'$concat': ['$site', '$article']}}},
            ],
            allowDiskUse=True,
        )
        prev_items = await prev_items.to_list(None)
        prev_items = {item['_id'] for item in prev_items}
        new_items = list(last_items - prev_items)
        if not (len(new_items) == 0 and depth < max_version):
            break
    new_items_ids = db.aggregate(
        [
            {'$match': {'version': {'$eq': max_version}}},
            {
                '$group': {
                    '_id': {'$concat': ['$site', '$article']},
                    'id': {'$last': '$_id'},
                },
            },
            {'$match': {'_id': {'$in': new_items}}},
        ],
        allowDiskUse=True,
    )
    new_items_ids = await new_items_ids.to_list(None)
    return [item['id'] for item in new_items_ids]