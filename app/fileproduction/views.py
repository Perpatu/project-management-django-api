"""
Views for the file APIs.
"""
import os

from app.settings import MEDIA_ROOT
from core.models import (
    FileProduction,
    CommentFileProduction,
    Task,
    NotificationTask,
    Department
)
from department.serializers import DepartmentSerializer
from fileproduction import serializers
from rest_framework import status
from rest_framework import (
    viewsets,
    mixins,
)
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .file_utils import (
    project_progress,
    get_file_project_data,
    tasks_dep_admin,
    files_dep_auth,
    search_files,
    notification_ws,
    update_task_project_ws,
    update_task_department_ws,
    task_permission_perform_create,
    task_in_create,
    task_in_destroy,
    task_in_update,
    uncheck_new_file_flag
)


class FileProductionAdminViewSet(mixins.DestroyModelMixin,
                                 mixins.CreateModelMixin,
                                 mixins.UpdateModelMixin,
                                 viewsets.GenericViewSet):
    """Manage file production APIs"""
    serializer_class = serializers.FileProductionManageSerializer
    queryset = FileProduction.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def destroy(self, request, *args, **kwargs):
        """Delete file object in db and file on server"""
        file = self.get_object()
        file_path = f'{MEDIA_ROOT}/{str(file.file)}'
        os.remove(file_path)
        file_data = serializers.FileProductionProjectSerializer(file).data
        super().destroy(request, *args, **kwargs)
        if file_data['tasks']:
            project_progress(file_data['project'])
        update_task_project_ws(file, 'file_delete')
        update_task_department_ws(file_data, 'file_delete')
        return Response({'FileProduction has been deleted'})

    def create(self, request, *args, **kwargs):
        """Create file object"""
        serializer = serializers.FilesUploadSerializer(data=request.data)
        if serializer.is_valid():
            qs = serializer.save()
            message = {'detail': qs, 'status': True}

            return Response(message, status=status.HTTP_201_CREATED)
        info = {'message': serializer.errors, 'status': False}
        return Response(info, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['GET'], detail=False, url_path='department')
    def file_department(self, request):
        """
            Returns info about department given it params dep_id, page_size,
            page_number and status_param
            and all files assigned to it
        """
        params = self.request.query_params
        data = tasks_dep_admin(params)
        return Response(data)

    @action(methods=['GET'], detail=False, url_path='columns-project')
    def file_mange_columns(self, request):
        """Columns for mange files"""

        deps = Department.objects.all()
        deps_ser = DepartmentSerializer(deps, many=True)
        deps_name = []
        for dep in deps_ser.data:
            deps_name.append(dep['name'])
        static_manage_columns = ['view', 'name', 'options']
        static_production_columns = ['view', 'name', 'comments']
        merged_manage_columns = static_manage_columns[0:2] + deps_name + [static_manage_columns[2]]
        merged_production_columns = static_production_columns[0:2] + deps_name + [static_production_columns[2]]
        result = {
            'departments': deps_ser.data,
            'manage_columns': merged_manage_columns,
            'production_columns': merged_production_columns
        }
        return Response(result)


class FileAuthViewSet(viewsets.GenericViewSet):
    """Manage file APIs"""
    serializer_class = serializers.FileProductionManageSerializer
    queryset = FileProduction.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @action(methods=['GET'], detail=False, url_path='department')
    def file_department(self, request):
        """
            Returns info about department given it params dep_id
            and all files assigned to it
        """
        params = self.request.query_params
        user_id = request.user.id
        data = files_dep_auth(params, user_id)
        return Response(data)

    @action(methods=['GET'], detail=False, url_path='department/search')
    def file_department_search(self, request):
        """
            Search
            Returns info about department given it params dep_id
            and all files assigned to it
        """
        params = self.request.query_params
        data = search_files(params)
        return Response(data)


class TaskViewSet(mixins.CreateModelMixin,
                  mixins.DestroyModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    """Manage task Logic for file APIs"""
    serializer_class = serializers.TaskManageSerializer
    queryset = Task.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def get_permissions(self):
        if self.action == 'update' or self.request.method == 'PATCH':
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'update' or self.request.method == 'PATCH':
            return serializers.TaskUpdateSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        """Creating task to file, calculate project progress and
            assing previous_task, next_task"""
        validated_data = serializer.validated_data
        dep_id = validated_data['department'].id
        file_id = validated_data['file'].id
        if Task.objects.filter(file=file_id, department=dep_id).exists():
            info = {'message': 'task with this department exists'}
            raise ValidationError(info)
        task_permission_perform_create(validated_data)
        return super().perform_create(serializer)

    def create(self, request, *args, **kwargs):
        """
            Creating task and updating next_task and previous_task and
            calculate project progress
        """
        response = super().create(request, *args, **kwargs)
        file = get_file_project_data(response.data['file'])
        current_task = task_in_create(response, file)
        response.data['next_task'] = current_task.next_task.id if current_task.next_task else None
        response.data['previous_task'] = current_task.previous_task.id if current_task.previous_task else None
        notification_ws(response.data)
        update_task_project_ws(file['id'], 'task')
        if file['new']:
            uncheck_new_file_flag(file['id'])
        return response

    def destroy(self, request, *args, **kwargs):
        """
            Delete task and updating next_task and previous_task and
            calculate project progress
        """
        task_obj = self.get_object()
        file = get_file_project_data(task_obj.file.id)

        tasks = file['tasks']
        task_ids = [task['id'] for task in tasks]
        task_index = task_ids.index(task_obj.id)
        task_in_destroy(tasks, task_index, task_obj)
        response = super().destroy(request, *args, **kwargs)
        if response.status_code == 204:
            update_task_project_ws(task_obj.file.id, 'task')
            project_progress(file['project'])
            return response
        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
            Update task and calculate project progress
        """
        request_data = request.data
        task_obj = self.get_object()

        if not task_obj.permission:
            info = {'message': 'task permission is False'}
            return Response(info)
        task_in_update(task_obj, request_data)
        response = super().update(request, *args, **kwargs)
        if response.status_code == 200:
            update_task_project_ws(task_obj.file.id, 'task')
            return response
        return super().update(request, *args, **kwargs)

    @action(methods=['GET'], detail=False, url_path='calendar')
    def users_task_calendar(self, request):
        """Return task for the user calendar"""
        user_id = self.request.query_params.get('user_id')
        queryset = self.queryset.filter(users__in=user_id, end=False)
        serializer = serializers.TaskCalendarSerializer(queryset, many=True)
        return Response(serializer.data)


class CommentFileViewSet(mixins.CreateModelMixin,
                         mixins.DestroyModelMixin,
                         viewsets.GenericViewSet):
    """Manage comments file APIs"""
    serializer_class = serializers.CommentFileDisplaySerializer
    queryset = CommentFileProduction.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'create' or self.action == 'destroy':
            return serializers.CommentFileProductionManageSerializer
        return self.serializer_class

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        update_task_project_ws(response.data['id'], 'comment_add')
        update_task_department_ws(response.data['id'], 'comment_add')
        return response

    def destroy(self, request, *args, **kwargs):
        user = request.user
        comment_object = self.get_object()
        comment_id = comment_object.id
        if not user.is_staff:
            if user.id == comment_object.user.id:
                update_task_project_ws(comment_id, 'comment_delete')
                update_task_department_ws(comment_id, 'comment_delete')
                return super().destroy(request, *args, **kwargs)
            else:
                info = {'message': 'This is not your comment'}
                return Response(info, status=status.HTTP_403_FORBIDDEN)
        update_task_project_ws(comment_id, 'comment_delete')
        update_task_department_ws(comment_id, 'comment_delete')
        return super().destroy(request, *args, **kwargs)


class NotificationsTaskView(mixins.ListModelMixin,
                            mixins.UpdateModelMixin,
                            viewsets.GenericViewSet):
    serializer_class = serializers.NotificationTaskSerializer
    queryset = NotificationTask.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """ Change queryset depending on action """
        if self.action == 'list':
            return self.queryset.filter(read=False, user=self.request.user)
        return super().get_queryset()

    @action(methods=['GET'], detail=False, url_path='quantity')
    def notification_task_quantity(self, request):
        """Return notification quantity"""
        quantity = self.queryset.filter(read=False, user=request.user).count()
        return Response(quantity)
