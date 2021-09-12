from pydantic import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения."""

    MONGODB_HOST: str = 'localhost'
    MONGODB_PORT: int = 27017
    MONGODB_DB: str = 'byshoes'
    MONGODB_USER: str = 'mongouser'
    MONGODB_PASSWORD: str = 'password'
    REDIS_URL: str = 'localhost'
    CRON_MINUTE: str = '0'
    CRON_HOUR: str = '*/12'
    CRON_DAY_OF_WEEK: str = '*'
    CRON_DAY_OF_MONTH: str = '*'
    CRON_MONTH_OF_YEAR: str = '*'


settings = Settings()
