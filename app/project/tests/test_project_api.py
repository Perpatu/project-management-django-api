"""
Test for project APIs
"""
from core.models import Project, Client
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from project.serializers import ProjectSerializer
from rest_framework import status
from rest_framework.test import APIClient

PROJECT_ADMIN_URL = reverse('project:admin-list')
PROJECT_EMPLOYEE_URL = reverse('project:auth-list')


def detail_employee_url(project_id):
    """Create and return a employee project detail URL"""
    return reverse('project:auth-detail', args=[project_id])


def detail_admin_url(project_id):
    """Create and return a admin project detail URL"""
    return reverse('project:admin-detail', args=[project_id])


def create_project(user, client_obj, **params):
    """Create and retrun a test client"""
    defaults = {
        'start': '2023-08-15',
        'deadline': '2023-10-15',
        'priority': 'In design',
        'number': 'Test number project'
    }
    defaults.update(params)

    project = Project.objects.create(
        manager=user,
        client=client_obj,
        **defaults
    )
    return project


def create_client(**params):
    """Create and retrun a test client"""
    defaults = {
        'name': 'Test name client',
        'email': 'clien@example.com',
        'phone_number': '+1 604 401 1234',
        'address': 'Test street 56',
    }
    defaults.update(params)

    client = Client.objects.create(**defaults)
    return client


def create_employee_user(**params):
    """Create and return a new employee user"""
    return get_user_model().objects.create_user(**params)


def create_admin_user(**params):
    """Create and return a new admin user"""
    return get_user_model().objects.create_superuser(**params)


class PublicProjectAPITests(TestCase):
    """Test unauthenticated API request"""

    def setUP(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API"""
        res = self.client.get(PROJECT_EMPLOYEE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateNotAdminProjectTests(TestCase):
    """Test authenticated and not admin API request"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_employee_user(
            email='user@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(self.user)

    def test_create_project(self):
        """Test creating project from not admin user"""
        client_obj = create_client()
        payload = {
            'manager': self.user,
            'client': client_obj,
            'start': '2023-08-19',
            'deadline': '2023-10-15',
            'priority': 'In design',
            'number': 'Test number project',
        }

        res = self.client.post(PROJECT_EMPLOYEE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_partial_update(self):
        """Test partial update project from not admin user"""
        client_obj = create_client()
        project = create_project(user=self.user, client_obj=client_obj)
        payload = {'number': 'Test number project 213e'}

        url = detail_employee_url(project.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_full_update(self):
        """Test full update project from not admin user"""
        client_obj = create_client()
        project = create_project(user=self.user, client_obj=client_obj)

        payload = {
            'manager': self.user,
            'client': client_obj,
            'start': '2023-07-15',
            'deadline': '2023-12-15',
            'priority': 'Completed',
            'number': 'Test number projectasdsad'
        }
        url = detail_employee_url(project.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_project(self):
        """Test deleting a project successful from not admin user"""
        client_obj = create_client()
        project = create_project(user=self.user, client_obj=client_obj)

        url = detail_employee_url(project.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_retrive_projects(self):
        """Test retrieving a list of projects to not admin user"""
        client_obj = create_client()
        create_project(user=self.user, client_obj=client_obj)
        create_project(user=self.user, client_obj=client_obj)

        res = self.client.get(PROJECT_EMPLOYEE_URL)

        projects = Project.objects.all().order_by('id')
        serializer = ProjectSerializer(projects, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


class PrivateAdminProjectTests(TestCase):
    """Test authenticated and admin API request"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_admin_user(
            email='user@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(self.user)

    def test_create_project(self):
        """Test creating project from admin user"""
        client_obj = create_client()
        payload = {
            'manager': self.user.id,
            'client': client_obj.id,
            'start': '2023-06-15',
            'deadline': '2023-07-15',
            'priority': 'Normal',
            'number': 'Test number asdasd',
        }

        res = self.client.post(PROJECT_ADMIN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_partial_update(self):
        """Test partial update project from admin user"""
        client_obj = create_client()
        project = create_project(user=self.user, client_obj=client_obj)

        payload = {'number': 'Test number project 213e'}
        url = detail_admin_url(project.id)

        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        project.refresh_from_db()
        self.assertEqual(project.manager, self.user)
        self.assertEqual(project.client, client_obj)
        self.assertEqual(project.start, project.start)
        self.assertEqual(project.deadline, project.deadline)
        self.assertEqual(project.progress, project.progress)
        self.assertEqual(project.priority, project.priority)
        self.assertEqual(project.status, project.status)
        self.assertEqual(project.number, payload['number'])
        self.assertEqual(project.secretariat, project.secretariat)
        self.assertEqual(project.invoiced, project.invoiced)

    def test_full_update(self):
        """Test full update project from admin user"""
        client_obj = create_client()
        project = create_project(user=self.user, client_obj=client_obj)

        payload = {
            'manager': self.user.id,
            'client': client_obj.id,
            'start': '2023-06-15',
            'deadline': '2023-07-15',
            'priority': 'Normal',
            'number': 'Test number asdasd',
        }

        url = detail_admin_url(project.id)
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # def test_delete_project(self):
        """Test deleting a project successful from admin user"""
        # client_obj = create_client()
        # project = create_project(user=self.user, client_obj=client_obj)

        # url = detail_admin_url(project.id)
        # res = self.client.delete(url)

        # self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        # self.assertFalse(Project.objects.filter(id=project.id).exists())

    def test_retrive_projects(self):
        """Test retrieving a list of projects to admin user"""
        client_obj = create_client()
        create_project(user=self.user, client_obj=client_obj)
        create_project(user=self.user, client_obj=client_obj)

        res = self.client.get(PROJECT_ADMIN_URL)

        projects = Project.objects.all().order_by('id')
        serializer = ProjectSerializer(projects, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
