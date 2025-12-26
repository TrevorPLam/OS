"""
Pagination guards for API list endpoints.
"""
from django.conf import settings
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination


class BoundedPageNumberPagination(PageNumberPagination):
    """PageNumberPagination with enforced maximum page size."""

    page_size_query_param = "page_size"
    page_size = settings.REST_FRAMEWORK.get("PAGE_SIZE", 50)
    max_page_size = getattr(settings, "API_PAGINATION_MAX_PAGE_SIZE", 200)

    def get_page_size(self, request):
        page_size = super().get_page_size(request)
        if page_size is None:
            return self.page_size

        if page_size <= 0:
            raise ValidationError({"page_size": "page_size must be a positive integer."})

        if self.max_page_size and page_size > self.max_page_size:
            raise ValidationError({
                "page_size": f"page_size exceeds maximum of {self.max_page_size}."
            })

        return page_size
