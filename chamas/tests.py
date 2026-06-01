from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from chamas.models import Chama, Membership


class ChamaTestCase(APITestCase):

    def setUp(self):
        """Create test users before each test"""
        self.admin = User.objects.create_user(
            username='0712100001',
            phone_number='0712100001',
            password='StrongPass123!'
        )
        self.member = User.objects.create_user(
            username='0712100002',
            phone_number='0712100002',
            password='StrongPass123!'
        )

    def test_create_chama(self):
        """Admin can create a new chama"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/chamas/', {
            'name': 'Test Chama',
            'description': 'A test chama',
            'contribution_amount': 1000,
            'frequency': 'monthly',
            'max_members': 10
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test Chama')
        # Creator is automatically made admin member
        self.assertTrue(
            Membership.objects.filter(
                user=self.admin,
                chama__name='Test Chama',
                role='admin'
            ).exists()
        )

    def test_create_chama_requires_auth(self):
        """Unauthenticated users cannot create a chama"""
        response = self.client.post('/api/chamas/', {
            'name': 'Ghost Chama',
            'contribution_amount': 1000,
            'frequency': 'monthly',
            'max_members': 10
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_join_chama(self):
        """A member can join an existing chama"""
        self.client.force_authenticate(user=self.admin)
        create = self.client.post('/api/chamas/', {
            'name': 'Join Test Chama',
            'contribution_amount': 500,
            'frequency': 'monthly',
            'max_members': 10
        })
        chama_id = create.data['id']

        self.client.force_authenticate(user=self.member)
        response = self.client.post(f'/api/chamas/{chama_id}/join/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['membership']['role'], 'member')

    def test_cannot_join_chama_twice(self):
        """A member cannot join the same chama twice"""
        self.client.force_authenticate(user=self.admin)
        create = self.client.post('/api/chamas/', {
            'name': 'Double Join Chama',
            'contribution_amount': 500,
            'frequency': 'monthly',
            'max_members': 10
        })
        chama_id = create.data['id']

        self.client.force_authenticate(user=self.member)
        self.client.post(f'/api/chamas/{chama_id}/join/')
        response = self.client.post(f'/api/chamas/{chama_id}/join/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_my_chamas(self):
        """Member can list their chamas"""
        chama = Chama.objects.create(
            name='My Chama',
            contribution_amount=1000,
            frequency='monthly',
            created_by=self.admin
        )
        Membership.objects.create(
            user=self.member,
            chama=chama,
            role='member'
        )
        self.client.force_authenticate(user=self.member)
        response = self.client.get('/api/chamas/my/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)