import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import UJSONResponse
from fastapi_pagination import add_pagination
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.middleware.cors import CORSMiddleware

from src.rest.endpoints import router
from src.settings import settings


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> UJSONResponse:
    """Make exception handler.

    Args:
        request: веб запрос
        exc: Исключение

    Returns:
        Обернутый HTTPException в виде UJSONResponse

    """
    err = exc.detail if isinstance(exc.detail, dict) else {'error': exc.detail}
    return UJSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(err),
    )

app = FastAPI(
    title='ByShoes',
)

app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


app.add_exception_handler(HTTPException, http_exception_handler)
add_pagination(app)


@app.on_event('startup')
async def startup_db_client():
    """Действия на запуск приложения."""
    app.mongodb_client = AsyncIOMotorClient(
        'mongodb://{0}:{1}@{2}:{3}/{4}'.format(
            settings.MONGODB_USER,
            settings.MONGODB_PASSWORD,
            settings.MONGODB_HOST,
            settings.MONGODB_PORT,
            settings.MONGODB_DB,
        ),
        tz_aware=True,
    )
    app.mongodb = app.mongodb_client[settings.MONGODB_DB]


@app.on_event('shutdown')
async def shutdown_db_client():
    """Действия на закрытие приложения."""
    app.mongodb_client.close()
