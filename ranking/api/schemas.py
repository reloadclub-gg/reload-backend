from typing import List

from ninja import Schema

from profiles.api.schemas import ProfileSchema


class RankingSchema(Schema):
    list: List[ProfileSchema] = []
    user: ProfileSchema = None
