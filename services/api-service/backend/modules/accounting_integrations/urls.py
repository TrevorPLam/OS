"""URL configuration for Accounting Integrations API."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AccountingOAuthConnectionViewSet,
    InvoiceSyncMappingViewSet,
    CustomerSyncMappingViewSet,
)

app_name = 'accounting_integrations'

router = DefaultRouter()
router.register(r'connections', AccountingOAuthConnectionViewSet, basename='connection')
router.register(r'invoice-mappings', InvoiceSyncMappingViewSet, basename='invoice-mapping')
router.register(r'customer-mappings', CustomerSyncMappingViewSet, basename='customer-mapping')

urlpatterns = [
    path('', include(router.urls)),
]
