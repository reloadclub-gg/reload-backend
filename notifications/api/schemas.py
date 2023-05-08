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
