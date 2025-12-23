"""
URL routes for Finance API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InvoiceViewSet, BillViewSet, LedgerEntryViewSet
from .payment_views import PaymentViewSet

router = DefaultRouter()
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'bills', BillViewSet, basename='bill')
router.register(r'ledger-entries', LedgerEntryViewSet, basename='ledgerentry')
router.register(r'payment', PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
]
