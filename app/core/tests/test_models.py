"""
Test models
"""
from core import models
from django.contrib.auth import get_user_model
from django.test import TestCase


def create_user(email='test@example.com', password='testpass123'):
    """Create and return a new user"""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    """Test models"""

    def test_create_user_with_email_successful(self):
        """Test creating user with email is successful"""

        email = 'test@example.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email normalized for new users"""
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com'],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'sample123')
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Test that creating a user without email raises a ValueError"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'test123')

    def test_create_superuser(self):
        """Test crating superuser"""
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'test123',
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_client(self):
        """Test creating client is successful"""
        client = models.Client.objects.create(
            name='Test name client',
            email='clien@example.com',
            phone_number='147852369',
            address='Test street 56',
        )

        self.assertEqual(str(client), client.name)

    def test_create_project(self):
        """Test creating project is successful"""
        user = create_user()

        client = models.Client.objects.create(
            name='Test name client',
            email='clien@example.com',
            phone_number='+1 604 401 1234',
            address='Test street 56',
        )
        project = models.Project.objects.create(
            manager=user,
            client=client,
            start='2023-09-12',
            deadline='2023-09-12',
            priority='Low',
            number='test 5876-78',
        )

        self.assertEqual(str(project), project.number)

    def test_create_commentProject(self):
        """Test creating commentProject is successful"""
        user = create_user()
        client = models.Client.objects.create(
            name='Test name client',
            email='clien@example.com',
            phone_number='+1 604 401 1234',
            address='Test street 56',
        )
        project = models.Project.objects.create(
            manager=user,
            client=client,
            start='2023-09-12',
            deadline='2023-09-12',
            priority='Low',
            number='test 5876-78',
        )
        commentProject = models.CommentProject.objects.create(
            user=user,
            project=project,
            text="Neque porro quisquam est qui dolorem ipsum \n"
                 "quia dolor sit amet, consectetur, adipisci velit...",
        )

        self.assertEqual(str(commentProject), commentProject.text)

    def test_create_department(self):
        """Test creating department is successful"""
        department = models.Department.objects.create(
            name='Test name department',
            order=1,
        )

        self.assertEqual(str(department), department.name)
