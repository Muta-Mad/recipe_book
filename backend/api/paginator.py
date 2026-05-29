from rest_framework.pagination import (
    PageNumberPagination as _PageNumberPagination,
)

from api.constants import PAGE_SIZE


class RecipeBookPagination(_PageNumberPagination):
    """Кастомная пагинация: page_size управляется параметром `limit`."""

    page_size = PAGE_SIZE
    page_size_query_param = 'limit'


# Backward-compatible alias
PageNumberPagination = RecipeBookPagination
