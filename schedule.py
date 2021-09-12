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
    'src.runners.parse_multisports': {'queue': 'multisports'},
    'src.runners.parse_allstars': {'queue': 'allstars'},
}

worker.conf.beat_schedule = {
    'parse-multisports': {
        'task': 'src.runners.parse_multisports',
        'schedule': crontab(
            month_of_year=settings.CRON_MONTH_OF_YEAR,
            day_of_month=settings.CRON_DAY_OF_MONTH,
            day_of_week=settings.CRON_DAY_OF_WEEK,
            hour=settings.CRON_HOUR,
            minute=settings.CRON_MINUTE,
        ),
    },
    'parse-allstrs': {
        'task': 'src.runners.parse_allstars',
        'schedule': crontab(
            month_of_year=settings.CRON_MONTH_OF_YEAR,
            day_of_month=settings.CRON_DAY_OF_MONTH,
            day_of_week=settings.CRON_DAY_OF_WEEK,
            hour=settings.CRON_HOUR,
            minute=settings.CRON_MINUTE,
        ),
    },
}
