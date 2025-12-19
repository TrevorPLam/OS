"""
DRF ViewSets for Finance module.
"""
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from modules.finance.models import Invoice, Bill, LedgerEntry
from .serializers import InvoiceSerializer, BillSerializer, LedgerEntrySerializer


class InvoiceViewSet(viewsets.ModelViewSet):
    """ViewSet for Invoice model."""
    queryset = Invoice.objects.select_related('client', 'project', 'created_by')
    serializer_class = InvoiceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'project', 'status']
    search_fields = ['invoice_number', 'client__company_name']
    ordering_fields = ['invoice_number', 'issue_date', 'due_date']
    ordering = ['-issue_date', '-created_at']


class BillViewSet(viewsets.ModelViewSet):
    """ViewSet for Bill model."""
    queryset = Bill.objects.select_related('project', 'approved_by')
    serializer_class = BillSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'expense_category', 'project']
    search_fields = ['reference_number', 'bill_number', 'vendor_name']
    ordering_fields = ['reference_number', 'bill_date', 'due_date']
    ordering = ['-bill_date', '-created_at']


class LedgerEntryViewSet(viewsets.ModelViewSet):
    """ViewSet for LedgerEntry model."""
    queryset = LedgerEntry.objects.select_related('invoice', 'bill', 'created_by')
    serializer_class = LedgerEntrySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['entry_type', 'account', 'transaction_group_id']
    search_fields = ['description', 'transaction_group_id']
    ordering_fields = ['transaction_date', 'created_at']
    ordering = ['-transaction_date', '-created_at']
