"""
Serializers for Client APIs
"""
from core.models import Client
from rest_framework import serializers


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for client"""

    class Meta:
        model = Client
        fields = '__all__'
        read_only_fields = ['id']


class ClientNestedSerializer(serializers.ModelSerializer):
    """Serializer for client"""

    class Meta:
        model = Client
        fields = ['id', 'name', 'color']
        read_only_fields = ['id']
