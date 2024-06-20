"""
Views for the document file APIs.
"""
import os
from app.settings import MEDIA_ROOT
from core.models import Document
from filedocument import serializers
from rest_framework import (
    viewsets,
    mixins,
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAdminUser


class FileDocumentAdminViewSet(mixins.DestroyModelMixin,
                               mixins.CreateModelMixin,
                               viewsets.GenericViewSet):
    """Manage file document APIs"""
    serializer_class = serializers.FileManageSerializer
    queryset = Document.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def create(self, request, *args, **kwargs):
        """Create file document object"""

        serializer = serializers.FilesUploadSerializer(data=request.data)
        if serializer.is_valid():
            qs = serializer.save()
            message = {'detail': qs, 'status': True}

            return Response(message, status=status.HTTP_201_CREATED)
        info = {'message': serializer.errors, 'status': False}
        return Response(info, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """Delete file document object in db and file on server"""
        file = self.get_object()
        file_path = f'{MEDIA_ROOT}/{str(file.file)}'
        os.remove(file_path)
        super().destroy(request, *args, **kwargs)
        return Response({'Document has been deleted'})
