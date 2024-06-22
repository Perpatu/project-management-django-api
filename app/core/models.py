"""
db models
"""
import os

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import CharField, TextField
from django.utils import timezone


class Department(models.Model):
    """Department Model"""
    name = models.CharField(max_length=255, blank=False, unique=True)
    order = models.IntegerField(unique=True, validators=[MinValueValidator(1)])
    date_add = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['name'])
        ]

    def __str__(self) -> CharField:
        return self.name


class UserManager(BaseUserManager):
    """Manager for user"""

    def create_user(self, username, role, password=None, **extra_fields):
        """create, save and return a new user"""
        if not username:
            raise ValueError('User must have username')
        if not password:
            raise ValueError('User must have password')

        departments = extra_fields.pop('departments', [])

        user = self.model(username=username, role=role, **extra_fields)
        if role == 'Admin':
            user.is_staff = True
        user.set_password(password)
        user.save(using=self._db)

        user.departments.set(departments)

        return user

    def create_superuser(self, username, password, role, email, first_name, last_name):
        """Create and return new superuser"""
        user = self.create_user(
            username=username,
            role=role,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """User in the system"""

    class UserRole(models.TextChoices):
        Admin = 'Admin'
        Employee = 'Employee'

    email = models.EmailField(max_length=255, unique=True)
    username = models.CharField(max_length=255, unique=True, blank=False)
    role = models.CharField(max_length=20, choices=UserRole.choices)
    first_name = models.CharField(max_length=255, blank=False)
    last_name = models.CharField(max_length=255, blank=False)
    phone_number = models.CharField(max_length=12, blank=True)
    address = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    departments = models.ManyToManyField(Department, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['role', 'email', 'first_name', 'last_name']

    class Meta:
        ordering = ['last_name']
        indexes = [
            models.Index(fields=['last_name'])
        ]


class Client(models.Model):
    """Client Model"""
    name = models.CharField(max_length=255, unique=True)
    email = models.EmailField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=12, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)
    date_add = models.DateField(auto_now_add=True)
    color = models.CharField(default="#3788D8", max_length=30, blank=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name'])
        ]

    def __str__(self) -> str:
        return self.name


class Project(models.Model):
    """Project Model"""

    class ProjectStatus(models.TextChoices):
        IN_DESIGN = 'In design'
        STARTED = 'Started'
        COMPLETED = 'Completed'
        SUSPENDED = 'Suspended'

    class InvoiceStatus(models.TextChoices):
        YES = 'YES'
        LACK_OF_INVOICE = 'YES (LACK OF INVOICE)'
        NO = 'NO'

    class Priority(models.TextChoices):
        HIGH = 'High'
        NORMAL = 'Normal'
        LOW = 'Low'

    manager = models.ForeignKey(User, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    start = models.DateField(blank=False)
    deadline = models.DateField(blank=False)
    progress = models.PositiveIntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ]
    )
    priority = models.CharField(max_length=20, choices=Priority.choices)
    status = models.CharField(
        max_length=20,
        default=ProjectStatus.IN_DESIGN,
        choices=ProjectStatus.choices
    )
    name = models.CharField(max_length=255, blank=False)
    number = models.CharField(max_length=255, blank=False)
    order_number = models.CharField(max_length=255, blank=True)
    secretariat = models.BooleanField(default=True)
    invoiced = models.CharField(
        max_length=30,
        default=InvoiceStatus.NO,
        choices=InvoiceStatus.choices
    )
    date_add = models.DateField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['number']),
            models.Index(fields=['manager']),
            models.Index(fields=['order_number']),
            models.Index(fields=['name']),
            models.Index(fields=['client']),
            models.Index(fields=['deadline'])
        ]

    def __str__(self) -> str:
        return self.number


class FileProduction(models.Model):
    """FileProduction model"""

    def file_path(self, filename):
        """Generate file path"""
        ext = os.path.splitext(filename)[1]
        filename = os.path.splitext(filename)[0] + ext
        return os.path.join(
            'uploads/projects',
            str(self.project.id),
            filename
        )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(
        Project,
        related_name='files',
        on_delete=models.CASCADE
    )

    name = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to=file_path, blank=False)
    date_add = models.DateField(default=timezone.now)
    new = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['file'])
        ]

    def __str__(self) -> str:
        return self.name


class Document(models.Model):
    """Documents model"""

    def file_path(self, filename):
        """Generate file path"""
        ext = os.path.splitext(filename)[1]
        filename = os.path.splitext(filename)[0] + ext
        return os.path.join(
            'uploads/projects',
            str(self.project.id),
            filename
        )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(
        Project,
        related_name='documents',
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to=file_path, blank=False)
    date_add = models.DateField(default=timezone.now)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['file'])
        ]

    def __str__(self) -> CharField:
        return self.name


class Task(models.Model):
    """Task model"""
    file = models.ForeignKey(
        FileProduction,
        related_name='tasks',
        on_delete=models.CASCADE
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    manager = models.ForeignKey(User, on_delete=models.CASCADE, blank=False)
    users = models.ManyToManyField(User, related_name='tasks', blank=True)
    planned_start_date = models.DateTimeField(blank=False)
    planned_end_date = models.DateTimeField(blank=False)
    real_start_date = models.DateTimeField(blank=True, null=True)
    real_end_date = models.DateTimeField(blank=True, null=True)
    paused_date = models.DateTimeField(blank=True, null=True)
    test = models.BooleanField(default=False)
    permission = models.BooleanField(default=False)
    start = models.BooleanField(default=False)
    paused = models.BooleanField(default=False)
    end = models.BooleanField(default=False)
    next_task = models.ForeignKey(
        'self',
        related_name='next',
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    previous_task = models.ForeignKey(
        'self',
        related_name='previous',
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    class Meta:
        ordering = ['department__order']
        indexes = [
            models.Index(fields=['department'])
        ]

    def __str__(self) -> str:
        return str(self.id)


class CommentFileProduction(models.Model):
    """Comment to FileProduction Model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.ForeignKey(
        FileProduction,
        related_name='comments',
        on_delete=models.CASCADE
    )
    text = models.TextField(blank=False)
    date_posted = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ['date_posted']
        indexes = [
            models.Index(fields=['date_posted'])
        ]

    def __str__(self) -> TextField:
        return self.text


class NotificationTask(models.Model):
    """Notification to QueueLogic Model"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    file = models.ForeignKey(FileProduction, on_delete=models.CASCADE)
    content = models.TextField()
    read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self) -> TextField:
        return self.content


class NotificationProject(models.Model):
    """Notification to Project Model"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    content = models.TextField()
    read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self) -> TextField:
        return self.content
