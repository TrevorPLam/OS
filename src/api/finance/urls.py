"""
URL routes for Finance API.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .payment_views import PaymentViewSet as StripePaymentViewSet
from .views import (
    BillViewSet,
    InvoiceViewSet,
    LedgerEntryViewSet,
    PaymentViewSet,
    PaymentAllocationViewSet,
    ProjectProfitabilityViewSet,
    ServiceLineProfitabilityViewSet,
)

router = DefaultRouter()
router.register(r"invoices", InvoiceViewSet, basename="invoice")
router.register(r"bills", BillViewSet, basename="bill")
router.register(r"ledger-entries", LedgerEntryViewSet, basename="ledgerentry")
router.register(r"stripe-payment", StripePaymentViewSet, basename="stripe-payment")  # Stripe payment processing
router.register(r"payments", PaymentViewSet, basename="payment")  # Cash application (Feature 2.10)
router.register(r"payment-allocations", PaymentAllocationViewSet, basename="payment-allocation")  # Feature 2.10
router.register(r"project-profitability", ProjectProfitabilityViewSet, basename="project-profitability")  # Task 3.3
router.register(r"service-line-profitability", ServiceLineProfitabilityViewSet, basename="service-line-profitability")  # Task 3.3

urlpatterns = [
    path("", include(router.urls)),
]
