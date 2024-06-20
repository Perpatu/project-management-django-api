"""
ULR mapping for the client app
"""
from client import views
from django.urls import (
    path,
    include
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('admin', views.ClientViewSet)

app_name = 'client'

urlpatterns = [
    path('', include(router.urls)),
]
