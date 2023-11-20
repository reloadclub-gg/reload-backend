import os

import celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = celery.Celery('reload', CELERY_ALWAYS_EAGER=settings.TEST_MODE)
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'clear_dodges': {
        'task': 'lobbies.tasks.clear_dodges',
        'schedule': crontab(minute=0, hour=0),
    },
    'decr_level_from_inactivity': {
        'task': 'accounts.tasks.decr_level_from_inactivity',
        'schedule': crontab(day_of_week='sunday'),
    },
    'queue': {
        'task': 'lobbies.tasks.queue',
        'schedule': 1.0,
    },
    'delete_old_cancelled_matches': {
        'task': 'matches.tasks.delete_old_cancelled_matches',
        'schedule': crontab(minute=0, hour=0),
    },
    'keep_alive': {
        'task': 'websocket.tasks.keep_alive',
        'schedule': 7.0,
    },
    'logout_inactive_users': {
        'task': 'accounts.tasks.logout_inactive_users',
        'schedule': crontab(minute=0, hour=0),
    },
}


@celery.signals.after_setup_logger.connect
def on_after_setup_logger(logger, **kwargs):
    logger.setLevel(settings.LOG_LEVEL)


app.autodiscover_tasks()
