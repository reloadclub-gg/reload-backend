import math
from typing import Any, List

from django.conf import settings
from ninja import Field, Schema
from ninja.pagination import PaginationBase


class Pagination(PaginationBase):
    class Input(Schema):
        page: int = Field(1, ge=1)

    def __init__(
        self, page_size: int = settings.PAGINATION_PER_PAGE, **kwargs: Any
    ) -> None:
        self.page_size = page_size
        super().__init__(**kwargs)

    class Output(Schema):
        results: List[Any]
        count: int
        page_size: int
        total_pages: int
        prev_page: int = None
        current_page: int
        next_page: int = None

    def paginate_queryset(self, queryset: Any, pagination: Input, **params: Any) -> Any:
        offset = (pagination.page - 1) * self.page_size
        total_pages = math.ceil(self._items_count(queryset) / self.page_size)
        prev_page = pagination.page - 1 if pagination.page > 1 else None
        next_page = pagination.page + 1 if pagination.page < total_pages else None
        paginated = offset + self.page_size
        results = queryset[offset:paginated]

        return {
            'results': results,
            'count': self._items_count(queryset),
            'page_size': self.page_size,
            'total_pages': total_pages,
            'prev_page': prev_page,
            'current_page': pagination.page,
            'next_page': next_page,
        }

    items_attribute: str = "results"
