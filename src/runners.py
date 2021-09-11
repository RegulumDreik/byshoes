from asgiref.sync import async_to_sync

from schedule import worker
from src.multisports.parse import parse_site


@worker.task
def parse_multisports():
    """Запуск парсинга сайта multisport."""
    print(1)
    async_to_sync(parse_site)()
