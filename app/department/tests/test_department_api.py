"""
Test for department APIs
"""
from core.models import Department
from department.serializers import DepartmentSerializer
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

DEPARTMENT_ADMIN_URL = reverse('department:admin-list')
DEPARTMENT_EMPLOYEE_URL = reverse('department:auth-list')


def detail_employee_url(department_id):
    """Create and return a employee department detail URL"""
    return reverse(
        'department:auth-detail', args=[department_id]
    )


def detail_admin_url(department_id):
    """Create and return a admin department detail URL"""
    return reverse(
        'department:admin-detail', args=[department_id]
    )


def create_employee_user(**params):
    """Create and return a new employee user"""
    return get_user_model().objects.create_user(**params)


def create_admin_user(**params):
    """Create and return a new admin user"""
    return get_user_model().objects.create_superuser(**params)


def create_department(**params):
    """Create and retrun a test department"""
    defaults = {
        'name': 'Test department',
        'order': 1,
    }
    defaults.update(params)

    department = Department.objects.create(
        **defaults
    )

    return department


class PublicDepartmentAPITests(TestCase):
    """Test unauthenticated API request"""

    def setUP(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API"""
        res = self.client.get(DEPARTMENT_EMPLOYEE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateNotAdminDepartmentTests(TestCase):
    """Test authenticated and not admin API request"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_employee_user(
            email='user@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(self.user)

    def test_create_department(self):
        """Test creating department from not admin user"""
        payload = {
            'name': 'Test department',
            'order': 1,
        }
        res = self.client.post(DEPARTMENT_EMPLOYEE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_partial_update(self):
        """Test partial update department from not admin user"""

        department = create_department(
            name='Test department',
            order=1,
        )
        payload = {'name': 'Test asdasd'}

        url = detail_employee_url(department.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_full_update(self):
        """Test full update department from not admin user"""

        department = create_department(
            name='Test department',
            order=1
        )
        payload = {
            'name': 'Test department asd',
            'order': 2,
        }
        url = detail_employee_url(department.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_department(self):
        """Test deleting a department successful from not admin user"""
        department = create_department(
            name='Test department',
            order=1,
        )

        url = detail_employee_url(department.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_retrive_department(self):
        """Test retrieving a list of department to not admin user"""
        create_department(
            name='Test department',
            order=1,
        )
        create_department(
            name='Test department das',
            order=2,
        )

        res = self.client.get(DEPARTMENT_EMPLOYEE_URL)

        projects = Department.objects.all().order_by('id')
        serializer = DepartmentSerializer(projects, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


class PrivateAdmindepartmentTests(TestCase):
    """Test authenticated and admin API request"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_admin_user(
            email='user@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(self.user)

    def test_create_department(self):
        """Test creating department from admin user"""
        payload = {
            'name': 'Test department',
            'order': 1,
        }
        res = self.client.post(DEPARTMENT_ADMIN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_partial_update(self):
        """Test partial update department from admin user"""

        department = create_department(
            name='Test department',
            order=1,
        )
        payload = {'name': 'Test asdasd'}

        url = detail_admin_url(department.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        department.refresh_from_db()
        self.assertEqual(department.name, payload['name'])
        self.assertEqual(department.order, department.order)

    def test_full_update(self):
        """Test full update department from admin user"""

        department = create_department(
            name='Test department',
            order=1
        )
        payload = {
            'name': 'Test department asd',
            'order': 2,
        }
        url = detail_admin_url(department.id)
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_delete_department(self):
        """Test deleting a department successful from admin user"""
        department = create_department(
            name='Test department',
            order=1,
        )

        url = detail_admin_url(department.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Department.objects.filter(id=department.id).exists())

    def test_retrive_department(self):
        """Test retrieving a list of department to admin user"""
        create_department(
            name='Test department',
            order=1,
        )
        create_department(
            name='Test department das',
            order=2,
        )

        res = self.client.get(DEPARTMENT_ADMIN_URL)

        projects = Department.objects.all().order_by('id')
        serializer = DepartmentSerializer(projects, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
