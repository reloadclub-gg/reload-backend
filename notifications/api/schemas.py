from django.utils import timezone
from ninja import Schema


class NotificationSchema(Schema):
    id: int
    to_user_id: int
    content: str
    avatar: str
    create_date: timezone.datetime
    from_user_id: int = None
    read_date: timezone.datetime = None

    @staticmethod
    def resolve_create_date(obj):
        return obj.create_date
