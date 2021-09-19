import asyncio
import itertools

from asgiref.sync import async_to_sync
from motor.motor_asyncio import AsyncIOMotorClient

from schedule import worker
from src.allstars.parse import parse_site as allstars
from src.multisports.parse import parse_site as multisports
from src.settings import settings
from src.utils.utils import get_max_version

PARSER_LIST = [multisports, allstars]


@worker.task
def parse_all():
    """Запуск парсинга сайта multisport."""
    async_to_sync(start_parse)()


async def start_parse():
    """Подшивает версию парсинга и запускает его."""
    mongodb_client = AsyncIOMotorClient(
        'mongodb://{0}:{1}@{2}:{3}/{4}'.format(
            settings.MONGODB_USER,
            settings.MONGODB_PASSWORD,
            settings.MONGODB_HOST,
            settings.MONGODB_PORT,
            settings.MONGODB_DB,
        ),
        tz_aware=True,
    )[settings.MONGODB_DB]['byshoes-collection']
    parse_version = await get_max_version(mongodb_client)
    tasks = [asyncio.ensure_future(parser()) for parser in PARSER_LIST]
    results = list(itertools.chain.from_iterable(await asyncio.gather(*tasks)))
    insert_result = []
    for item in results:
        if item is not None:
            item['version'] = parse_version + 1
            insert_result.append(item)
    await mongodb_client.insert_many(insert_result)
