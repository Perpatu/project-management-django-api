"""
URL mappings for the user API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(
    '',
    views.UserViewSet,
    basename=''
)

router.register(
    'manage',
    views.UserTestViewSet,
    basename='manage'
)

app_name = 'user'

urlpatterns = [
    path('create/', views.CreateUserView.as_view(), name='create'),
    path('token/', views.CreateTokenView.as_view(), name='token'),
    path('manage/', views.ManagerUserView.as_view(), name='manage'),
    path('', include(router.urls)),
]
