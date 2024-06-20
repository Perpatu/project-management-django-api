"""
Django admin customization
"""

from core import models
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _


class UserAdmin(BaseUserAdmin):
    """Define the admin pages for users"""
    ordering = ['id']
    list_display = ['username', 'email', 'first_name', 'last_name', 'role']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (
            _('Permissons'),
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'role',
                    'departments'
                )
            }
        ),
        (
            _('About user'),
            {
                'fields': (
                    'username',
                    'first_name',
                    'last_name'
                )
            }
        ),
        (_('Important dates'), {'fields': ('last_login',)}),
    )
    readonly_fields = ['last_login']
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'password1',
                'password2',
                'role',
                'username',
                'first_name',
                'last_name',
                'departments',
                'is_active',
                'is_staff',
                'is_superuser',
            )
        }),
    )


admin.site.register(models.User, UserAdmin)
admin.site.register(models.Client)
admin.site.register(models.Project)
admin.site.register(models.CommentFileProduction)
admin.site.register(models.Document)
admin.site.register(models.FileProduction)
admin.site.register(models.Task)
admin.site.register(models.Department)
admin.site.register(models.NotificationTask)
admin.site.register(models.NotificationProject)
