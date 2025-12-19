"""
DRF Serializers for CRM module.
"""
from rest_framework import serializers
from modules.crm.models import Client, Proposal, Contract


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ProposalSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.company_name', read_only=True)

    class Meta:
        model = Proposal
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'sent_at', 'accepted_at']


class ContractSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.company_name', read_only=True)
    proposal_number = serializers.CharField(source='proposal.proposal_number', read_only=True)

    class Meta:
        model = Contract
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
