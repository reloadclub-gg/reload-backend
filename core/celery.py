import logging
import os

import celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = celery.Celery('gta', CELERY_ALWAYS_EAGER=settings.TEST_MODE)
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {}


@celery.signals.after_setup_logger.connect
def on_after_setup_logger(**kwargs):
    logger = logging.getLogger('celery')
    logger.propagate = True
    logger = logging.getLogger('celery.app.trace')
    logger.propagate = True


app.autodiscover_tasks()
