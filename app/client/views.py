"""
Views for the client APIs.
"""
from client import serializers
from core.models import Client
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .client_utils import search_client


class ClientViewSet(viewsets.ModelViewSet):
    """View for manage client APIs"""
    serializer_class = serializers.ClientSerializer
    queryset = Client.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        return super().perform_create(serializer)

    @action(methods=['GET'], detail=False, url_path='columns')
    def client_columns(self, request):
        """Columns for client"""
        columns = ['name', 'email',
                   'phone', 'address',
                   'date_add', 'color', 'options']
        return Response(columns)

    @action(methods=['GET'], detail=False, url_path='search')
    def client_search_view(self, request):
        """Search client"""
        params = self.request.query_params
        response = search_client(params)
        return response
