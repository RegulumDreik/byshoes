import asyncio
import json
import logging
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from fastapi.encoders import jsonable_encoder
from httpx import Response
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import HttpUrl

from src.enums import SexEnum
from src.models import Category, ProductModelParse, Size, Specification
from src.settings import settings

spec_mapper = {
    'пол': 'sex',
    'цвет': 'color',
    'артикул': 'article',
}
logger = logging.getLogger(__name__)


async def parse_site():
    """Функция запускает парсинг сайта."""
    print('Start parsing allstars.')
    parse_addreses = [
        '/store/men/shoes/',
        '/store/women/shoes/',
    ]
    tasks = [parse_main_page(page) for page in parse_addreses]
    main_page_set = set()
    results = await asyncio.gather(*tasks)
    for result in results:
        main_page_set = main_page_set | result
    print(len(main_page_set))
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
    tasks = []
    for page in main_page_set:
        task = asyncio.ensure_future(
            parse_product_page(
                page,
                mongodb_client,
            ),
        )
        await asyncio.sleep(1)
        tasks.append(task)
    await asyncio.gather(*tasks)
    print('Finish parsing multisports.')


async def parse_main_page(start_page: str) -> set[str]:
    """Функция парсит постранично страницу с моделями.

    Args:
        start_page: Адрес начальный страницы.

    Returns:
        Список ссылок на отдельные модели для дальнейшего парсинга.

    """
    print(f'Start parsing {start_page}.')
    next_page = start_page
    uniq_pages = set()
    async with httpx.AsyncClient(base_url='https://all-stars.by') as client:
        while next_page:
            try:
                response = await client.get(next_page)
            except httpx.ReadTimeout:
                response = await client.get(next_page)
            soup = BeautifulSoup(response.text, 'lxml')
            next_page = get_next_page(soup)
            cards: list[BeautifulSoup] = soup.findAll(
                'article',
                {'class': 's_item'},
            )
            for item in cards:
                uniq_pages.add(
                    item.findNext(
                        'div',
                        {'class': 's_item-det'},
                    ).findNext(
                        'a',
                    ).attrs.get('href'),
                )
    print(f'Finish parsing {start_page}.')
    return uniq_pages


async def parse_product_page(
    url: str,
    db: AsyncIOMotorClient,
):
    """Парсит страницу продкута и записывает в базу информацию.

    Args:
        url: Ссылка на страницу продукта.
        db: Коннект к базе данных

    """
    print(f'Start parsing {url}.')
    async with httpx.AsyncClient(base_url='https://all-stars.by') as client:
        response: Response = await client.get(url)
        while response.status_code != 200:
            print(f'Responce is not correct: {response}.')
            await asyncio.sleep(3)
            response = await client.get(url)
        soup = BeautifulSoup(response.text, 'lxml')
        price = soup.find(
            'button',
            {'class': 'js-add-cart'},
        ).attrs['data-price']
        old_price = soup.find(
            'button',
            {'class': 'js-add-cart'},
        ).attrs['data-oldprice']
        try:
            pm = ProductModelParse(
                title=soup.find('meta', {'itemprop': 'name'}).attrs['content'],
                images=get_images(soup, str(client.base_url)),
                link=str(client.base_url) + url,
                price=price,
                discounted_price=old_price if old_price != price else None,
                category=get_categories(soup),
                site='allstars',
                article=get_article(soup),
                specification=get_specification(soup),
            )
        except ValidationError as exc:
            print(exc.json())
            print('error on' + str(client.base_url) + url)
            return
        await db.insert_one(jsonable_encoder(pm, by_alias=True))
        print(f'Finish parsing {url}.')


def get_categories(page: BeautifulSoup) -> list[Category]:
    """Парсинг карточки с информацией о продукте.

    Args:
        page: Страница для парсинга.

    Returns:
        Информация о продукте.
    """
    content = page.find('div', {'class': 'breadcrumbs'}).findAll('a')
    out = []
    out.append(Category(id='obuv', name='обувь'))
    out.append(Category(
        id=content[-1].attrs['href'].split('/')[-2],
        name=content[-1].attrs['title'].strip().lower(),
    ))
    return out


def get_specification(page: BeautifulSoup) -> Specification:
    """Парсинг карточки с информацией о продукте.

    Args:
        page: Страница для парсинга.

    Returns:
        Информация о продукте.
    """
    content = page.find('div', {'class': 'content-container'})
    return Specification(
        color=get_color(content),
        sex=get_sex(content),
        size=get_sizes(content),
    )


def get_sizes(page: BeautifulSoup) -> list[Size]:  # noqa: C901
    """Парсит карточку размеров продкута.

    Args:
        page: Страница для парсинга.

    Returns:
        Список размеров.
    """
    well_known_keys = ('data-us', 'data-eu', 'data-uk', 'data-ru', 'data-cm')
    sizes_block = page.findAll('a', {'class': 'js-size-type'})
    size_merged = {}
    for size in sizes_block:
        for key, value in size.attrs.items():
            if key not in size_merged:
                size_merged[key] = []
            size_merged[key].append(value)
    out = []
    for key, value in size_merged.items():
        if key in well_known_keys:
            try:
                out.append(Size(
                    size_type=key.split('-')[-1],
                    values=value,
                ))
            except ValidationError:
                continue
    return out


def get_color(page: BeautifulSoup) -> str:
    """Парсинг в поисках цвета.

    Args:
        page: Страница для парсинга.

    Returns:
        наименование цвета.
    """
    return json.loads(page.find(
        'button', {'class': 'js-add-cart'},
    ).attrs.get(
        'data-pixel-add-items-to-cart',
    )).get('color')


def get_article(page: BeautifulSoup) -> str:
    """Парсинг в поисках цвета.

    Args:
        page: Страница для парсинга.

    Returns:
        наименование цвета.
    """
    return json.loads(page.find(
        'button', {'class': 'js-add-cart'},
    ).attrs.get(
        'data-pixel-add-items-to-cart',
    )).get('article')


def get_sex(page: BeautifulSoup) -> SexEnum:
    """Парсинг в поисках цвета.

    Args:
        page: Страница для парсинга.

    Returns:
        наименование цвета.
    """
    return encode_sex(page.find(
        'div', {'class': 'subtitle'},
    ).text)


def encode_sex(sex: str) -> SexEnum:
    """Переводит пол из того что записано на сайте, в енум.

    Args:
        sex: Пол с сайта.

    Returns:
        Пол по енуму.
    """
    sex = sex.strip().lower()
    if sex == 'для мужчин' or sex == 'для мальчиков':
        return SexEnum.MALE
    if sex == 'для женщин' or sex == 'для девочек':
        return SexEnum.FEMALE
    return SexEnum.UNISEX


def get_next_page(page: BeautifulSoup) -> Optional[str]:
    """Находит следующую страницу на главной.

    Args:
        page: Страница для парсинга.

    Returns:
        Ссылку на следующую страницу.
    """
    pagination = page.findAll('nav', {'class': 'pages'})
    if len(pagination) == 0:
        return None
    next_page_tag = pagination[0].findNext(
        'a',
        {'aria-label': 'Next'},
    )
    if next_page_tag is None:
        return None
    else:
        return next_page_tag.attrs.get('href')


def get_images(page: BeautifulSoup, base_url: str) -> list[HttpUrl]:
    """Парсит страницу для получения ссылок на картинки модели.

    Args:
        page: Страница для парсинга.
        base_url: Базовый url для подшивания в адреса.

    Returns:
        Список ссылок на картинки.
    """
    image_rotator = page.find('ul', {'class': 'js-images-main'}).findAll('img')
    images = []
    for img in image_rotator:
        images.append(base_url + img.attrs['src'])
    return images
