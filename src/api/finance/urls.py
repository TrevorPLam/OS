"""
URL routes for Finance API.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .payment_views import PaymentViewSet
from .views import BillViewSet, InvoiceViewSet, LedgerEntryViewSet

router = DefaultRouter()
router.register(r"invoices", InvoiceViewSet, basename="invoice")
router.register(r"bills", BillViewSet, basename="bill")
router.register(r"ledger-entries", LedgerEntryViewSet, basename="ledgerentry")
router.register(r"payment", PaymentViewSet, basename="payment")

urlpatterns = [
    path("", include(router.urls)),
]
