from asgiref.sync import async_to_sync

from schedule import worker
from src.allstars.parse import parse_site as allstars
from src.multisports.parse import parse_site as multisports


@worker.task
def parse_multisports():
    """Запуск парсинга сайта multisport."""
    async_to_sync(multisports)()


@worker.task
def parse_allstars():
    """Запуск парсинга сайта allstars."""
    async_to_sync(allstars)()
