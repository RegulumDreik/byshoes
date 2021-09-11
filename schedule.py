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
        'schedule': crontab(hour='*/12', minute=0),
    },
    'parse-allstrs': {
        'task': 'src.runners.parse_allstars',
        'schedule': crontab(hour='*/12', minute=0),
    },
}
