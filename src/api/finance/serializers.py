"""
DRF Serializers for Finance module.
"""
from rest_framework import serializers
from modules.finance.models import Invoice, Bill, LedgerEntry


class InvoiceSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.company_name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    balance_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class BillSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    balance_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Bill
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'approved_at']


class LedgerEntrySerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    bill_reference = serializers.CharField(source='bill.reference_number', read_only=True)

    class Meta:
        model = LedgerEntry
        fields = '__all__'
        read_only_fields = ['created_at']
