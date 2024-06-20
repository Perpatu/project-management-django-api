"""
Serializers for department APIs
"""

from core.models import Department, Task
from rest_framework import serializers


class QueueLogicToFileSerializer(serializers.ModelSerializer):
    """Serializer for queue logic in FileProduction"""

    class Meta:
        model = Task
        exclude = ['file', ]
        read_only_fields = ['id']


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department"""

    class Meta:
        model = Department
        fields = ['id', 'name', 'order']
        read_only_fields = ['id']


class DepartmentListSerializer(serializers.ModelSerializer):
    """Serializer for Department"""

    class Meta:
        model = Department
        fields = ['id', 'name', 'order']
        read_only_fields = ['id']


class DepartmentStatsSerializer(serializers.ModelSerializer):
    """Serializer for stats departments"""

    department = DepartmentSerializer(many=False)

    class Meta:
        model = Task
        fields = ['department', ]
