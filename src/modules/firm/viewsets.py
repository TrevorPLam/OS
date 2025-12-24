from django.core.exceptions import FieldDoesNotExist, ValidationError


class FirmScopedViewSetMixin:
    firm_lookup = "firm"
    client_lookup = None
    client_param = "client_id"
    client_param_alias = "client"

    def get_firm(self):
        return getattr(self.request, "firm", None)

    def filter_by_firm(self, queryset):
        firm = self.get_firm()
        if firm is None:
            return queryset.none()
        return queryset.filter(**{self.firm_lookup: firm})

    def get_client_id(self):
        return (
            self.request.query_params.get(self.client_param)
            or self.request.query_params.get(self.client_param_alias)
        )

    def resolve_client_lookup(self, queryset):
        if self.client_lookup:
            return self.client_lookup
        try:
            queryset.model._meta.get_field("client")
        except FieldDoesNotExist:
            return None
        return "client_id"

    def filter_by_client(self, queryset):
        client_id = self.get_client_id()
        if not client_id:
            return queryset
        client_lookup = self.resolve_client_lookup(queryset)
        if not client_lookup:
            return queryset
        return queryset.filter(**{client_lookup: client_id})

    def get_queryset(self):
        queryset = self.filter_by_firm(super().get_queryset())
        return self.filter_by_client(queryset)

    def assign_firm(self, serializer):
        firm = self.get_firm()
        if firm is None:
            raise ValidationError("Firm context is required.")
        serializer.save(**{self.firm_lookup: firm})

    def perform_create(self, serializer):
        self.assign_firm(serializer)
