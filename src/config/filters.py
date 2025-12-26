"""
Filter backends with guardrails for expensive query parameters.
"""

from django.conf import settings
from rest_framework import filters
from rest_framework.exceptions import ValidationError


class BoundedSearchFilter(filters.SearchFilter):
    """SearchFilter that enforces a maximum search term length."""

    max_search_length = getattr(settings, "API_SEARCH_MAX_LENGTH", 100)

    def get_search_terms(self, request):
        raw_term = request.query_params.get(self.search_param, "")
        if raw_term and len(raw_term) > self.max_search_length:
            raise ValidationError(
                {self.search_param: (f"Search term exceeds maximum length of {self.max_search_length} characters.")}
            )
        return super().get_search_terms(request)
