"""
ULR mapping for the department app
"""

from department import views
from django.urls import (
    path,
    include
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(
    'admin',
    views.DepartmentAdminViewSet,
    basename='admin'
)
router.register(
    'auth',
    views.DepartmentAuthViewSet,
    basename='auth'
)
app_name = 'department'

urlpatterns = [
    path('', include(router.urls)),
]
