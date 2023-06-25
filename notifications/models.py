from __future__ import annotations

from typing import List

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import m2m_changed
from django.templatetags.static import static
from django.utils import timezone
from django.utils.translation import gettext as _
from pydantic import BaseModel

from appsettings.services import (
    max_notification_history_count_per_player as notification_limit,
)
from core.redis import RedisClient
from core.utils import str_to_timezone
from websocket.utils import ws_send

from .api.schemas import NotificationSchema

cache = RedisClient()
User = get_user_model()


class NotificationError(Exception):
    pass


class SystemNotification(models.Model):
    AVATAR = static('icons/logo_icon.png')

    to_users = models.ManyToManyField(User, blank=True)
    content = models.TextField()
    create_date = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.content


class Notification(BaseModel):
    """
    This model represents the notifications on Redis cache db.
    We store `MAX_NOTIFICATIONS_HISTORY` notifications per user.

    The Redis db keys from this model are described below:

    [key]   __mm:notifications:auto_id int
    [zset]  __mm:notifications:player:[player_id] <id: int, create_date: timestamp>
    [hash]  __mm:notifications:[id] <{
        id: int
        from_user_id: int
        to_user_id: int
        content: str
        create_date: timezone.datetime
        read_date: timezone.datetime
        avatar: str
    }>
    """

    id: int
    to_user_id: int
    content: str
    avatar: str
    from_user_id: int = None
    read_date: timezone.datetime = None

    class Config:
        CACHE_PREFIX: str = '__mm:notifications'

    @property
    def cache_key(self) -> str:
        return f'{Notification.Config.CACHE_PREFIX}:{self.id}'

    @property
    def create_date(self) -> timezone.datetime:
        return str_to_timezone(cache.hget(self.cache_key, 'create_date'))

    def save(self) -> bool:
        existing_entry = cache.hgetall(self.cache_key)
        now = timezone.now()
        if not existing_entry:
            create_date = now.isoformat()
        else:
            create_date = existing_entry.get('create_date')

        hash = {
            'id': self.id,
            'to_user_id': self.to_user_id,
            'content': self.content,
            'create_date': create_date,
            'avatar': self.avatar,
        }

        if self.from_user_id:
            hash.update({'from_user_id': self.from_user_id})

        if self.read_date:
            hash.update({'read_date': self.read_date.isoformat()})

        cache.hmset(
            self.cache_key,
            hash,
        )

        if not existing_entry:
            notifications_count = cache.zcount(
                f'__mm:notifications:player:{self.to_user_id}', '-inf', '+inf'
            )

            if notifications_count >= notification_limit():
                popped = cache.zpopmin(
                    f'__mm:notifications:player:{self.to_user_id}', 1
                )
                notification = Notification.get_by_id(popped[0][0])
                cache.delete(notification.cache_key)

            cache.zadd(
                f'__mm:notifications:player:{self.to_user_id}',
                {self.id: now.timestamp()},
            )

        created = not existing_entry
        return (created, self)

    def mark_as_read(self):
        self.read_date = timezone.now()
        self.save()

    @staticmethod
    def incr_auto_id() -> int:
        return int(cache.incr('__mm:notifications:auto_id'))

    @staticmethod
    def get_auto_id() -> int:
        count = cache.get('__mm:notifications:auto_id')
        return int(count) if count else 0

    @staticmethod
    def create_system_notifications(
        content: str,
        avatar: str,
        to_user_ids: List[int],
    ) -> List[Notification]:
        notifications = list()
        for to_id in to_user_ids:
            n = Notification.create(content, avatar, to_id)
            notifications.append(n)

        return notifications

    @staticmethod
    def create(
        content: str,
        avatar: str,
        to_user_id: int,
        from_user_id: int = None,
    ) -> Notification:
        auto_id = Notification.incr_auto_id()
        notification = Notification(
            id=auto_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            content=content,
            avatar=avatar,
        )
        notification.save()
        return notification

    @staticmethod
    def get_all_by_user_id(user_id: int) -> List[Notification]:
        results = cache.zrange(f'__mm:notifications:player:{user_id}', 0, -1)
        return [Notification.get_by_id(result) for result in results]

    @staticmethod
    def get_by_id(id: int) -> Notification:
        result = cache.hgetall(f'__mm:notifications:{id}')
        if not result:
            raise NotificationError(_('Notification not found.'))

        return Notification(**result)


def system_notification_to_users_changed(sender, instance, action, **kwargs):
    if action == 'post_add':
        to_users_ids = list(
            User.objects.filter(pk__in=kwargs.get('pk_set')).values_list(
                'pk', flat=True
            )
        )
        notifications = Notification.create_system_notifications(
            content=instance.content,
            avatar=SystemNotification.AVATAR,
            to_user_ids=to_users_ids,
        )

        # send websockets here because there is no way to import
        # ws_send_notification without circular import
        for notification in notifications:
            payload = NotificationSchema.from_orm(notification).dict()
            async_to_sync(ws_send)(
                'notifications/add',
                payload,
                groups=[notification.to_user_id],
            )


m2m_changed.connect(
    system_notification_to_users_changed,
    sender=SystemNotification.to_users.through,
)
