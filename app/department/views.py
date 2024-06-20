"""
Views for the department APIs.
"""

from core.models import (
    Department,
    Task,
)
from department import serializers
from rest_framework import (
    viewsets,
    mixins,
)
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response


class DepartmentAdminViewSet(mixins.CreateModelMixin,
                             mixins.DestroyModelMixin,
                             mixins.ListModelMixin,
                             mixins.RetrieveModelMixin,
                             mixins.UpdateModelMixin,
                             viewsets.GenericViewSet):
    """View for manage admin department APIs"""
    serializer_class = serializers.DepartmentSerializer
    queryset = Department.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        """Create a new department"""
        serializer.save()

    @action(methods=['GET'], detail=False, url_path='stats')
    def department_admin_stats(self, request):
        """Returns a list of how much files are assigned to department"""
        queryset = Task.objects.filter(end=False)
        serializer = serializers.DepartmentStatsSerializer(queryset, many=True)
        data = serializer.data
        dep_info_dict = {}

        for item in data:
            dep_info = item["department"]
            dep_id = dep_info["id"]
            dep_name = dep_info["name"]

            if dep_name in dep_info_dict:
                dep_info_dict[dep_name]["quantity"] += 1
            else:
                dep_info_dict[dep_name] = {
                    "id": dep_id,
                    "quantity": 1,
                    "name": dep_name
                }

        result = list(dep_info_dict.values())
        return Response(result)


class DepartmentAuthViewSet(mixins.RetrieveModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    """View for auth users department APIs"""
    serializer_class = serializers.DepartmentStatsSerializer
    queryset = Task.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        """Returns departments list where user has permission"""
        user = request.user
        user_deps = []
        for dep in user.departments.values():
            user_deps.append(dep['id'])
        queryset = Department.objects.filter(id__in=user_deps)
        serializer = serializers.DepartmentListSerializer(queryset, many=True)
        data = serializer.data
        return Response(data)

    @action(methods=['GET'], detail=False, url_path='stats')
    def department_stats(self, request):
        """Returns a list of how much files are assigned to department where user has permission"""
        user = request.user
        user_deps = []
        for dep in user.departments.values():
            user_deps.append(dep['id'])
        queryset = self.queryset.filter(department__in=user_deps, users__in=[user.id], end=False)
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        dep_info_dict = {}

        for item in data:
            dep_info = item["department"]
            dep_id = dep_info["id"]
            dep_name = dep_info["name"]

            if dep_name in dep_info_dict:
                dep_info_dict[dep_name]["quantity"] += 1
            else:
                dep_info_dict[dep_name] = {
                    "id": dep_id,
                    "quantity": 1,
                    "name": dep_name
                }

        result = list(dep_info_dict.values())
        return Response(result)
