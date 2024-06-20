"""
ULR mapping for the project app
"""

from django.urls import (
    path,
    include
)
from project import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(
    'production',
    views.ProjectProductionViewSet,
    basename='production'
)
router.register(
    'secretariat',
    views.ProjectSecretariatViewSet,
    basename='secretariat'
)
router.register(
    'notification',
    views.NotificationsProjectView,
    basename='notification'
)

app_name = 'project'

urlpatterns = [
    path('', include(router.urls)),
]
