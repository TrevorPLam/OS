"""
DRF Serializers for Assets module.
"""
from rest_framework import serializers
from modules.assets.models import Asset, MaintenanceLog


class AssetSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)

    class Meta:
        model = Asset
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class MaintenanceLogSerializer(serializers.ModelSerializer):
    asset_tag = serializers.CharField(source='asset.asset_tag', read_only=True)
    asset_name = serializers.CharField(source='asset.name', read_only=True)

    class Meta:
        model = MaintenanceLog
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
