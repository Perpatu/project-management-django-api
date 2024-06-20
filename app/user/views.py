"""
Views for the user API
"""
from core.models import User
from django.db.models import Q
from rest_framework import generics, authentication, permissions
from rest_framework import (
    viewsets,
    mixins,
)
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.settings import api_settings
from user.serializers import (
    UserSerializer,
    AuthTokenSerializer,
    UserBoardSerializer
)


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system"""
    serializer_class = UserSerializer


class CreateTokenView(ObtainAuthToken):
    """Create a new auth token for user"""
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManagerUserView(generics.RetrieveAPIView):
    """Manage the authenticated user"""
    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retrieve and return the authenticated user"""
        return self.request.user


class UserViewSet(mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    """View for users APIs"""
    serializer_class = UserSerializer
    queryset = User.objects.all()
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'list':
            return UserBoardSerializer
        return super().get_serializer_class()

    @action(methods=['GET'], detail=False, url_path='admin')
    def user_admin_view(self, request):
        """Return admin users"""
        queryset = self.queryset.filter(role='Admin')
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False, url_path='not-admin')
    def user_employee_view(self, request):
        """Return employee users"""
        queryset = self.queryset.filter(role='Employee')
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False, url_path='assigned-employee')
    def user_employee_assigned_department_view(self, request):
        """Return employee users assigned to department"""
        dep_id = self.request.query_params.get('dep_id')
        queryset = self.queryset.filter(role='Employee', departments__in=dep_id)
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False, url_path='search')
    def user_search_view(self, request):
        """Search users using q param"""
        query = self.request.query_params.get('q')
        queryset = self.queryset.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(role__icontains=query))
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False, url_path='columns')
    def user_columns_view(self, request):
        """Return columns users"""
        data = ['last_name', 'status', 'username', 'email', 'role', 'address', 'departments', 'options']
        return Response(data)


class UserTestViewSet(mixins.UpdateModelMixin,
                      mixins.DestroyModelMixin,
                      viewsets.GenericViewSet):
    """View for users APIs"""
    serializer_class = UserSerializer
    queryset = User.objects.all()
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAdminUser]

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
