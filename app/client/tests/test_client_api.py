"""
Tests for Client APIs
"""
from client.serializers import ClientSerializer
from core.models import Client
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

CLIENT_URL = reverse('client:client-list')


def detail_url(client_id):
    """Create and return a client detail URL"""
    return reverse('client:client-detail', args=[client_id])


def create_client(**params):
    """Create and retrun a test client"""
    defaults = {
        'email': 'clien@example.com',
        'phone_number': '+1 604 401 1234',
        'address': 'Test street 56',
    }
    defaults.update(params)

    client = Client.objects.create(**defaults)
    return client


def create_user(**params):
    """Create and return a new user"""
    return get_user_model().objects.create_user(**params)


class PublicClientAPITests(TestCase):
    """Test unauthenticated API request"""

    def setUP(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API"""
        res = self.client.get(CLIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateAdminClientAPITests(TestCase):
    """Test authenticated and admin API request"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email='user@example.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        self.client.force_authenticate(self.user)

    def test_retrive_clients_for_admin(self):
        """Test list of clients is limited to admin users"""
        create_client(name='Test1 name client')
        create_client(name='Test2 name client')

        res = self.client.get(CLIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_get_client_detail(self):
        """Test get client detail"""
        client_obj = create_client(name='Test3 name client')

        url = detail_url(client_obj.id)
        res = self.client.get(url)

        serializer = ClientSerializer(client_obj)
        self.assertEqual(res.data, serializer.data)

    def test_create_client(self):
        """Test creating a client"""
        payload = {
            'name': 'Test4 name client',
            'email': 'client@example.com',
            'phone_number': '+1 604 401 1234',
            'address': 'Test street 56',
        }
        res = self.client.post(CLIENT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        client_obj = Client.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(client_obj, k), v)

    def test_partial_update(self):
        """Test partial update of a client"""
        original_address = 'Test street 56'
        client_obj = create_client(
            name='Test5 name client',
            email='client@example.com',
            address=original_address
        )

        payload = {'address': 'Example street 154'}
        url = detail_url(client_obj.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        client_obj.refresh_from_db()
        self.assertEqual(client_obj.name, client_obj.name)
        self.assertEqual(client_obj.email, client_obj.email)
        self.assertEqual(client_obj.address, payload['address'])

    def test_full_update(self):
        """Test full update client"""
        client_obj = create_client(
            name='Test6 name client',
            email='client@example.com',
            phone_number='+1 604 401 1234',
            address='Test street 56',
            color='#ff0000'
        )

        payload = {
            'name': 'Test6 name client',
            'email': 'client@test.com',
            'phone_number': '+48 789 256 987',
            'address': 'example street 106',
            'color': '#0000FF'
        }

        url = detail_url(client_obj.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        client_obj.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(client_obj, k), v)

    def test_delete_client(self):
        """Test deleting a client successful"""
        client_obj = create_client(name='Test7 name client')

        url = detail_url(client_obj.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Client.objects.filter(id=client_obj.id).exists())


class PrivateNotAdminClientAPITests(TestCase):
    """Test authenticated and not admin API request"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email='user@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(self.user)

    def test_retrive_clients_for_not_admin(self):
        """Test list of clients is limited to auth but not admin users"""
        create_client(name='Test8 name client')
        create_client(name='Test9 name client')

        res = self.client.get(CLIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
