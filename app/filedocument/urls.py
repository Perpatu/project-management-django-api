"""
ULR mapping for the file document app
"""

from django.urls import (
    path,
    include
)
from filedocument import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(
    'admin',
    views.FileDocumentAdminViewSet,
    basename='admin'
)

app_name = 'filedocument'

urlpatterns = [
    path('', include(router.urls)),
]