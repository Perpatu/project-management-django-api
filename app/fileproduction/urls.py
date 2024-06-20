"""
ULR mapping for the file production app
"""
from django.urls import (
    path,
    include
)
from fileproduction import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(
    'admin',
    views.FileProductionAdminViewSet,
    basename='admin'
)
router.register(
    'auth',
    views.FileAuthViewSet,
    basename='auth'
)
router.register(
    'comments',
    views.CommentFileViewSet,
    basename='comments'
)
router.register(
    'task',
    views.TaskViewSet,
    basename='task'
)
router.register(
    'noti',
    views.NotificationsTaskView,
    basename='noti'
)

app_name = 'fileproduction'

urlpatterns = [
    path('', include(router.urls)),
]
