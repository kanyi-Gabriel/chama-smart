from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User


class UserRegistrationTest(APITestCase):

    def test_register_success(self):
        """A new user can register with valid data"""
        response = self.client.post('/api/accounts/register/', {
            'phone_number': '0712000001',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'id_number': '11111111'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertEqual(response.data['user']['phone_number'], '0712000001')

    def test_register_password_mismatch(self):
        """Registration fails when passwords don't match"""
        response = self.client.post('/api/accounts/register/', {
            'phone_number': '0712000002',
            'email': 'test2@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'StrongPass123!',
            'password2': 'WrongPass123!',
            'id_number': '22222222'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_phone(self):
        """Registration fails with duplicate phone number"""
        User.objects.create_user(
            username='0712000003',
            phone_number='0712000003',
            password='StrongPass123!'
        )
        response = self.client.post('/api/accounts/register/', {
            'phone_number': '0712000003',
            'email': 'other@example.com',
            'first_name': 'Other',
            'last_name': 'User',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'id_number': '33333333'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        """User can login with correct credentials"""
        User.objects.create_user(
            username='0712000004',
            phone_number='0712000004',
            password='StrongPass123!'
        )
        response = self.client.post('/api/accounts/login/', {
            'phone_number': '0712000004',
            'password': 'StrongPass123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_login_wrong_password(self):
        """Login fails with wrong password"""
        User.objects.create_user(
            username='0712000005',
            phone_number='0712000005',
            password='StrongPass123!'
        )
        response = self.client.post('/api/accounts/login/', {
            'phone_number': '0712000005',
            'password': 'WrongPassword!'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_requires_authentication(self):
        """Profile endpoint rejects unauthenticated requests"""
        response = self.client.get('/api/accounts/profile/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_returns_user_data(self):
        """Authenticated user can view their profile"""
        user = User.objects.create_user(
            username='0712000006',
            phone_number='0712000006',
            password='StrongPass123!'
        )
        self.client.force_authenticate(user=user)
        response = self.client.get('/api/accounts/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['phone_number'], '0712000006')