import logging
import os

import celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = celery.Celery('gta', CELERY_ALWAYS_EAGER=settings.TEST_MODE)
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'clear_dodges': {
        'task': 'matchmaking.tasks.clear_dodges',
        'schedule': crontab(minute=0, hour=0),
    },
    'decr_level_from_inactivity': {
        'task': 'accounts.tasks.decr_level_from_inactivity',
        'schedule': crontab(day_of_week='sunday'),
    },
}


@celery.signals.after_setup_logger.connect
def on_after_setup_logger(**kwargs):
    logger = logging.getLogger('celery')
    logger.propagate = True
    logger = logging.getLogger('celery.app.trace')
    logger.propagate = True


app.autodiscover_tasks()
