from pydantic import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения."""

    MONGODB_HOST: str = 'localhost'
    MONGODB_PORT: int = 27017
    MONGODB_DB: str = 'byshoes'
    MONGODB_USER: str = 'mongouser'
    MONGODB_PASSWORD: str = 'password'
    REDIS_URL: str = 'localhost'


settings = Settings()
