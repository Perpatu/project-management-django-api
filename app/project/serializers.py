"""
Serializers for Project APIs
"""
from client.serializers import ClientNestedSerializer
from core.models import (
    Project,
    NotificationProject
)
from fileproduction.serializers import FileProductionProjectSerializer
from filedocument.serializers import FileDocumentProjectSerializer
from rest_framework import serializers
from user.serializers import UserNestedSerializer


class ProjectCreateSerializer(serializers.ModelSerializer):
    """Serializer create project"""

    class Meta:
        model = Project
        fields = [
            'id',
            'manager',
            'client',
            'start',
            'deadline',
            'priority',
            'progress',
            'name',
            'number',
            'order_number',
            'status',
        ]
        read_only_fields = ['id']

    def to_representation(self, instance):
        response = super().to_representation(instance)
        first_name = UserNestedSerializer(instance.manager).data['first_name']
        last_name = UserNestedSerializer(instance.manager).data['last_name']
        response['manager'] = {
            'id': UserNestedSerializer(instance.manager).data['id'],
            'name': first_name[0].upper() + '. ' + last_name
        }
        response['client'] = {
            'id': ClientNestedSerializer(instance.client).data['id'],
            'name': ClientNestedSerializer(instance.client).data['name'],
            'color': ClientNestedSerializer(instance.client).data['color'],
        }
        return response


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for project"""

    class Meta:
        model = Project
        fields = [
            'id',
            'manager',
            'client',
            'start',
            'deadline',
            'progress',
            'priority',
            'status',
            'name',
            'number',
            'order_number',
            'secretariat',
            'invoiced',
        ]
        read_only_fields = ['id']

    def to_representation(self, instance):
        response = super().to_representation(instance)
        first_name = UserNestedSerializer(instance.manager).data['first_name']
        last_name = UserNestedSerializer(instance.manager).data['last_name']
        response['manager'] = {
            'id': UserNestedSerializer(instance.manager).data['id'],
            'name': first_name[0].upper() + '. ' + last_name
        }
        response['client'] = {
            'id': ClientNestedSerializer(instance.client).data['id'],
            'name': ClientNestedSerializer(instance.client).data['name'],
            'color': ClientNestedSerializer(instance.client).data['color'],
        }
        return response


class ProjectDetailSerializer(ProjectSerializer):
    """Serializer for project detail view."""
    files = FileProductionProjectSerializer(many=True)
    documents = FileDocumentProjectSerializer(many=True)

    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ['files', 'documents']


class ProjectSecretariatDetailSerializer(ProjectSerializer):
    """Serializer for project detail view."""
    documents = FileDocumentProjectSerializer(many=True)

    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ['files', 'documents']


class ProjectProgressSerializer(serializers.ModelSerializer):
    """Serializer for project"""

    class Meta:
        model = Project
        fields = ['id', 'progress', 'status']


class NotificationProjectSerializer(serializers.ModelSerializer):
    """Serializer for project"""

    class Meta:
        model = NotificationProject
        fields = '__all__'
        read_only_fields = ['id']
