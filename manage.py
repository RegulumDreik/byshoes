import asyncio
import logging

import click
import uvicorn

from src.allstars.parse import parse_site as allstars
from src.multisports.parse import parse_site as multisports


@click.group()
@click.pass_context
def main(ctx: click.core.Context) -> None:
    """Инициализация контекстного менеджера.

    Args:
        ctx: контекстный менеджер

    """


@main.command()
@click.option('--port', '-p', default=8080)
@click.option('--host', '-h', default='localhost')
@click.pass_context
def runserver(ctx: click.core.Context, port: int, host: str) -> None:
    """Запуск web-части приложения.

    Args:
        ctx: контекстный менеджер
        port: порт для запуска приложения, по умолчанию '8080'
        host: хост для запуска приложения, по умолчанию 'localhost'

    """
    logging.basicConfig(format='%(asctime)-15s %(message)s', level=20)
    uvicorn.run('app:app', host=host, port=port, reload=True)


@main.command()
@click.pass_context
def startparse(ctx: click.core.Context) -> None:
    """Запуск web-части приложения.

    Args:
        ctx: контекстный менеджер

    """
    logging.basicConfig(format='%(asctime)-15s %(message)s', level=20)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(multisports())
    loop.run_until_complete(allstars())


if __name__ == '__main__':
    main()
