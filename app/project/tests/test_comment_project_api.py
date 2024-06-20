"""
Test for comment project APIs
"""
from core.models import CommentProject, Client, Project
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from project.serializers import CommentProjectDisplaySerializer
from rest_framework import status
from rest_framework.test import APIClient

COMMENT_PROJECT_URL = reverse('project:comments-list')


def detail_comment_url(comment_id):
    """Create and return a comment detail url."""
    return reverse('project:comments-detail', args=[comment_id])


def create_user(email='user@example.com', password='testpass123'):
    """Create and return a new user"""
    return get_user_model().objects.create_user(email, password)


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


def create_project(user, **params):
    """Create and retrun a test client"""
    client_obj = create_client()

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


class PublicCommentProjectApiTests(TestCase):
    """Test unauthenticated API request"""

    def setUP(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API"""
        res = self.client.get(COMMENT_PROJECT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateCommentProjectApiTests(TestCase):
    """Test authenticated API request"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrive_commentprojects(self):
        """Test retrieving a list of comment projects"""
        project = create_project(user=self.user)
        CommentProject.objects.create(
            user=self.user,
            project=project,
            text='Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n'
                 'Nullam et enim blandit, mattis magna quis,\n'
                 'elementum risus. Duis ipsum ex.'
        )
        CommentProject.objects.create(
            user=self.user,
            project=project,
            text='Lorem ipsum dolor sit amet, consectetur adipiscing elit.'
        )

        res = self.client.get(COMMENT_PROJECT_URL)
        comments = CommentProject.objects.all().order_by('-date_posted')
        serializer = CommentProjectDisplaySerializer(comments, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_delete_comment(self):
        """Test deleting comment"""
        project = create_project(user=self.user)
        comment = CommentProject.objects.create(
            user=self.user,
            project=project,
            text='Nullam et enim blandit, mattis magna quis.'
        )

        url = detail_comment_url(comment.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        comments = CommentProject.objects.filter(id=comment.id)
        self.assertFalse(comments.exists())

    def test_create_comment(self):
        """Test creating project from admin user"""
        project = create_project(user=self.user)
        payload = {
            'user': self.user.id,
            'project': project.id,
            'text': 'Nullam et enim blandit, mattis magna quis.',
        }

        res = self.client.post(COMMENT_PROJECT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
