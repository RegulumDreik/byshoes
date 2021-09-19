import logging

from celery import Celery
from celery.schedules import crontab

from src.settings import settings

logging.basicConfig(format='%(asctime)-15s %(message)s', level=20)

worker = Celery(
    'scheduler',
    broker='redis://{0}:6379/0'.format(settings.REDIS_URL),
    include=['src.runners'],
)
worker.conf.task_routes = {
    'src.runners.parse_all': {'queue': 'all'},
}

worker.conf.beat_schedule = {
    'parse-all': {
        'task': 'src.runners.parse_all',
        'schedule': crontab(
            month_of_year=settings.CRON_MONTH_OF_YEAR,
            day_of_month=settings.CRON_DAY_OF_MONTH,
            day_of_week=settings.CRON_DAY_OF_WEEK,
            hour=settings.CRON_HOUR,
            minute=settings.CRON_MINUTE,
        ),
    },
}
