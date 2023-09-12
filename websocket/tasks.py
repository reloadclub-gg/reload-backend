from celery import shared_task

from core.websocket import ws_ping


@shared_task
def keep_alive():
    ws_ping()
