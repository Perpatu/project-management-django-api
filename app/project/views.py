import os
import shutil

from app.settings import MEDIA_ROOT
from core.models import Project, NotificationProject
from project import serializers
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .project_utils import (
    filter_production_projects,
    search_projects,
    filter_secretariat_projects,
    search_secretariat_projects,
    notification_ws,
    project_data_ws
)


class ProjectProductionViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.ProjectSerializer
    queryset = Project.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        """ Change Serializer depending on action """

        if self.action == 'create':
            return serializers.ProjectCreateSerializer
        elif self.action == 'retrieve':
            return serializers.ProjectDetailSerializer
        return self.serializer_class

    def retrieve(self, request, *args, **kwargs):
        """ Returns project detail view with files management """

        response = super().retrieve(request, *args, **kwargs)
        data = response.data
        return Response(data)

    def update(self, request, *args, **kwargs):
        """ Updates project """

        if 'status' in request.data and request.data['status'] == 'Completed':
            request.data.update({'progress': 100})

        response = super().update(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            project_data_ws(response.data, response.data['status'], 'update')
        return super().update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """ Create project and send notification """

        if request.data['status'] == 'Completed':
            request.data.update({'progress': 100})
        response = super().create(request, *args, **kwargs)

        if response.status_code == status.HTTP_201_CREATED:
            notification_ws(response.data)
            project_data_ws(response.data, response.data['status'], 'create')
        return response

    def destroy(self, request, *args, **kwargs):
        """ Delete project """

        project = self.get_object()
        dir_path = os.path.join(
            MEDIA_ROOT,
            'uploads',
            'projects',
            str(project.id)
        )

        if os.path.isdir(dir_path):
            shutil.rmtree(dir_path)

        response = super().destroy(request, *args, **kwargs)

        if response.status_code == status.HTTP_204_NO_CONTENT:
            project_data_ws(project, project.status, 'delete')

        return response

    @action(methods=['GET'], detail=False, url_path='board')
    def board_view(self, request):
        """
            Returns all project with given status in params
            'Active': ['Started', 'In design'](default),
            'My_Active': ['Started', 'In design'],
            'My_Completed': ['Completed'],
            'My_Suspended': ['Suspended'],
            'Suspended': ['Suspended'],
            'Completed': ['Completed'],
        """

        user = request.user
        params = self.request.query_params
        data = filter_production_projects(self.queryset, params, user)

        if data is None:
            info = {'message': 'There is no such project status'}
            return Response(info, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(data)

    @action(methods=['GET'], detail=False, url_path='search')
    def search_view(self, request):
        """
            Returns a list of projects depending on status and the expression entered in search params
        """

        user = request.user
        params = self.request.query_params
        data = search_projects(params, user)

        if data is None:
            info = {'message': 'There is no such project status'}
            return Response(info, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(data)


class ProjectSecretariatViewSet(
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.ProjectSerializer
    queryset = Project.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        """ Change Serializer depending on action """

        if self.action == 'retrieve':
            return serializers.ProjectSecretariatDetailSerializer
        return self.serializer_class

    def retrieve(self, request, *args, **kwargs):
        """ Returns project detail view with files management """

        response = super().retrieve(request, *args, **kwargs)
        data = response.data
        return Response(data)

    @action(methods=['GET'], detail=False, url_path='board')
    def board_view(self, request):
        """
            Returns all project with given status in params
            'YES': ['YES', 'YES (LACK OF INVOICE)'],
            'NO': ['NO'],
        """

        user = request.user
        params = self.request.query_params
        data = filter_secretariat_projects(self.queryset, params, user)
        return Response(data)

    @action(methods=['GET'], detail=False, url_path='search')
    def search_view(self, request):
        """
            Returns all project in secretariat with given status in params
            NO(default), YES, YES (LACK OF INVOICE)
        """

        user = request.user
        params = self.request.query_params
        data = search_secretariat_projects(params, user)
        return Response(data)


class NotificationsProjectView(
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.NotificationProjectSerializer
    queryset = NotificationProject.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        """ Change queryset depending on action """
        if self.action == 'list':
            return self.queryset.filter(read=False, user=self.request.user)
        return super().get_queryset()

    @action(methods=['GET'], detail=False, url_path='quantity')
    def notification_task_quantity(self, request):
        """ Return unread notification quantity """

        quantity = self.queryset.filter(read=False, user=request.user).count()
        return Response(quantity)
