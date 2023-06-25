from django.conf import settings
from ninja import Schema


class NotificationSchema(Schema):
    id: int
    to_user_id: int
    content: str
    avatar: str
    create_date: str
    from_user_id: int = None
    read_date: str = None

    @staticmethod
    def resolve_create_date(obj):
        return obj.create_date.isoformat()

    @staticmethod
    def resolve_read_date(obj):
        return obj.read_date.isoformat() if obj.read_date else None

    @staticmethod
    def resolve_avatar(obj):
        if not obj.from_user_id:
            if settings.ENVIRONMENT == settings.LOCAL:
                return settings.SITE_URL + obj.avatar

        return obj.avatar


class NotificationUpdateSchema(Schema):
    read_date: str = None
