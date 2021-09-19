import asyncio
import logging
from typing import Any, Optional, Set, Tuple, Union

import httpx
from bs4 import BeautifulSoup, Tag
from fastapi.encoders import jsonable_encoder
from httpx import Response
from pydantic import HttpUrl, ValidationError

from src.enums import SexEnum
from src.models import Category, ProductModelParse, Size, Specification

spec_mapper = {
    'пол': 'sex',
    'цвет': 'color',
    'артикул': 'article',
}
logger = logging.getLogger(__name__)


async def parse_site():
    """Функция запускает парсинг сайта.

    Returns:
        Список спаршенных сущностей.
    """
    print('Start parsing multisports.')
    parse_addreses = [
        '/catalog/muzhchiny/obuv/',
        '/catalog/zhenshchiny/obuv/',
        '/catalog/muzhchiny/obuv/botinki/',
        '/catalog/muzhchiny/obuv/slantsy_i_sandalii/',
        '/catalog/muzhchiny/obuv/futbolnye_butsy/',
        '/catalog/muzhchiny/obuv/krossovki/',
        '/catalog/zhenshchiny/obuv/kedy/',
        '/catalog/zhenshchiny/obuv/krossovki_vysokie/',
        '/catalog/zhenshchiny/obuv/sapogi_i_botinki/',
        '/catalog/zhenshchiny/obuv/slantsy-i-sandalii/',
    ]
    tasks = [parse_main_page(page) for page in parse_addreses]
    main_page_set = set()
    results = await asyncio.gather(*tasks)
    for result in results:
        main_page_set = main_page_set | result
    unic = remove_duplicates(main_page_set)
    tasks = []
    for page in unic:
        task = asyncio.ensure_future(
            parse_product_page(
                page['url'],
                page['categories'],
            ),
        )
        await asyncio.sleep(1)
        tasks.append(task)
    print('Finish parsing multisports.')
    return await asyncio.gather(*tasks)


async def parse_main_page(start_page: str) -> set:
    """Функция парсит постранично страницу с моделями.

    Args:
        start_page: Адрес начальный страницы.

    Returns:
        Список ссылок на отдельные модели для дальнейшего парсинга.

    """
    print(f'Start parsing {start_page}.')
    next_page = start_page
    uniq_pages = set()
    async with httpx.AsyncClient(base_url='https://multisports.by') as client:
        while next_page:
            try:
                response = await client.get(next_page)
            except httpx.ReadTimeout:
                response = await client.get(next_page)
            soup = BeautifulSoup(response.text, 'lxml')
            next_page = get_next_page(soup)
            category = Category(
                id=start_page.split('/')[-2],
                name=soup.findAll(
                    'a',
                    {'href': start_page},
                )[-1].text.strip(),
            )
            cards: list[BeautifulSoup] = soup.findAll(
                'div',
                {'class': 'wrap-product-card'},
            )
            for item in cards:
                uniq_pages.add(
                    (
                        item.findNext(
                            'a',
                            {'class': 'product-name'},
                        ).attrs.get('href'),
                        category,
                    ),
                )
    print(f'Finish parsing {start_page}.')
    return uniq_pages


async def parse_product_page(
    url: str,
    categories: set[Category],
) -> dict[str, Any]:
    """Парсит страницу продкута и записывает в базу информацию.

    Args:
        url: Ссылка на страницу продукта.
        categories: Список категорий.

    Returns:
        Спаршенная сущность.
    """
    print(f'Start parsing {url}.')
    async with httpx.AsyncClient(base_url='https://multisports.by') as client:
        response: Response = await client.get(url)
        while response.status_code != 200:
            print(f'Responce is not correct: {response}.')
            await asyncio.sleep(3)
            response = await client.get(url)
        soup = BeautifulSoup(response.text, 'lxml')
        card_info = get_card_info(soup)
        card_info['size'] = get_sizes(soup)
        try:
            pm = ProductModelParse(
                title=get_title(soup),
                images=get_images(soup, str(client.base_url)),
                link=str(client.base_url) + url,
                price=get_price(soup),
                discounted_price=get_discounted_price(soup),
                category=categories,
                site='multisports',
                article=card_info['article'],
                specification=Specification.parse_obj(card_info),
            )
        except ValidationError as exc:
            print(exc.json())
            print('error on' + str(client.base_url) + url)
            return
        print(f'Finish parsing {url}.')
        return jsonable_encoder(pm, by_alias=True)


def get_card_info(page: BeautifulSoup) -> dict[str, Any]:
    """Парсинг карточки с информацией о продукте.

    Args:
        page: Страница для парсинга.

    Returns:
        Информация о продукте.
    """
    card_info: Tag = page.findAll('div', {'class': 'wrap-card-info'}).pop()
    out = {}
    for span in card_info.findAll('span'):
        row = span.text.lower().split(':')
        if row[0] not in spec_mapper.keys():
            continue
        key = spec_mapper[row[0]]
        if key == 'sex':
            row[1] = encode_sex(row[1])
        if key == 'color':
            row[1] = [row[1]]
        out[key] = row[1]
    return out


def encode_sex(sex: str) -> str:
    """Переводит пол из того что записано на сайте, в енум.

    Args:
        sex: Пол с сайта.

    Returns:
        Пол по енуму.
    """
    sex = sex.strip()
    if sex == 'мужчины' or sex == 'мальчики':
        return SexEnum.MALE.value
    if sex == 'женщины' or sex == 'девочки':
        return SexEnum.FEMALE.value
    return SexEnum.UNISEX.value


def get_sizes(page: BeautifulSoup) -> list[Size]:
    """Парсит карточку размеров продкута.

    Args:
        page: Страница для парсинга.

    Returns:
        Список размеров.
    """
    sizes_block: Tag = page.findAll('ul', {'class': 'list-sizes'}).pop()
    sizes = []
    if sizes_block is None:
        return []
    for li in sizes_block.findAll('li'):
        if not li.text.strip():
            continue
        sizes.append(float(li.text.strip().replace(',', '.')))
    sizes.sort()
    if len(sizes) == 0:
        return []
    return [Size(
        size_type='ru' if sizes[-1] > 20 else 'us',
        values=sizes,
    )]


def get_price(page: BeautifulSoup) -> Optional[float]:
    """Парсит карточку с ценой.

    Args:
        page: Страница для парсинга.

    Returns:
        Цена.
    """
    price_block: Tag = page.findAll('div', {'class': 'price-list'}).pop()
    card_info = price_block.findAll('span', {'class': 'cur-price'})
    if len(card_info) == 0:
        return None
    card_info = card_info.pop()
    return float(card_info.text.strip().split(' ')[0])


def get_discounted_price(page: BeautifulSoup) -> Optional[float]:
    """Парсит карточку с ценой для поиска цены до скидки.

    Args:
        page: Страница для парсинга.

    Returns:
        Цена до скидки.
    """
    price_block: Tag = page.findAll('div', {'class': 'price-list'}).pop()
    card_info = price_block.findAll('span', {'class': 'old-price'})
    if len(card_info) == 0:
        return None
    card_info = card_info.pop()
    return float(card_info.text.strip().split(' ')[0])


def get_title(page: BeautifulSoup) -> str:
    """Парсит карточку в поисках названия.

    Args:
        page: Страница для парсинга.

    Returns:
        Название модели.
    """
    title_tag: Tag = page.findAll(
        'div',
        {'class': 'wrap-product-card-name'},
    ).pop()
    return title_tag.text.strip()


def get_next_page(page: BeautifulSoup) -> Optional[str]:
    """Находит следующую страницу на главной.

    Args:
        page: Страница для парсинга.

    Returns:
        Ссылку на следующую страницу.
    """
    pagination = page.findAll('div', {'class': 'pagination'})
    if len(pagination) == 0:
        return None
    next_page_tag = pagination[0].findNext(
        'a',
        {'title': 'Следующая страница'},
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
    image_rotator = page.findAll('div', {'class': 'main-image'}).pop()
    images = []
    for img in image_rotator.findAll('img'):
        images.append(base_url + img.attrs['src'])
    return images


def remove_duplicates(
    urls: Set[Tuple[str, Category]],
) -> list[dict[str, Union[str, set[Category]]]]:
    """Удаляет дубликаты моделей из списка ссылок, сохраняет категории.

    Args:
        urls: Список ссылок для обработки.

    Returns:
        Список ссылок для дальнейшего парсинга.
    """
    unic_item_urls = {}
    for url in urls:
        object_name = url[0].split('/')[-2]
        if object_name in unic_item_urls.keys():
            unic_item_urls[object_name]['categories'].add(url[1])
            continue
        unic_item_urls[object_name] = {
            'url': url[0],
            'categories': {url[1]},
        }
    return list(unic_item_urls.values())
