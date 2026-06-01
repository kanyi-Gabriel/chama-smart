from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from chamas.models import Chama, Membership
from loans.models import LoanApplication


class LoanTestCase(APITestCase):

    def setUp(self):
        """Set up chama with admin and member"""
        self.admin = User.objects.create_user(
            username='0712200001',
            phone_number='0712200001',
            password='StrongPass123!'
        )
        self.member = User.objects.create_user(
            username='0712200002',
            phone_number='0712200002',
            password='StrongPass123!'
        )
        self.chama = Chama.objects.create(
            name='Loan Test Chama',
            contribution_amount=1000,
            frequency='monthly',
            created_by=self.admin
        )
        Membership.objects.create(
            user=self.admin,
            chama=self.chama,
            role='admin'
        )
        Membership.objects.create(
            user=self.member,
            chama=self.chama,
            role='member'
        )

    def test_apply_for_loan(self):
        """Member can apply for a loan"""
        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            f'/api/loans/chama/{self.chama.id}/apply/', {
                'amount_requested': 3000,
                'purpose': 'Business capital',
                'repayment_period_months': 3
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['loan']['status'], 'pending')
        self.assertIn('ml_info', response.data)

    def test_cannot_apply_twice(self):
        """Member cannot have two active loans"""
        self.client.force_authenticate(user=self.member)
        self.client.post(
            f'/api/loans/chama/{self.chama.id}/apply/', {
                'amount_requested': 3000,
                'purpose': 'First loan',
                'repayment_period_months': 3
            }
        )
        response = self.client.post(
            f'/api/loans/chama/{self.chama.id}/apply/', {
                'amount_requested': 1000,
                'purpose': 'Second loan',
                'repayment_period_months': 1
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_can_approve_loan(self):
        """Admin can approve a pending loan"""
        loan = LoanApplication.objects.create(
            applicant=self.member,
            chama=self.chama,
            amount_requested=2000,
            purpose='Test',
            status='pending'
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(f'/api/loans/{loan.id}/review/', {
            'action': 'approve',
            'amount_approved': 2000
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        loan.refresh_from_db()
        self.assertEqual(loan.status, 'approved')

    def test_admin_can_reject_loan(self):
        """Admin can reject a pending loan"""
        loan = LoanApplication.objects.create(
            applicant=self.member,
            chama=self.chama,
            amount_requested=2000,
            purpose='Test',
            status='pending'
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(f'/api/loans/{loan.id}/review/', {
            'action': 'reject'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        loan.refresh_from_db()
        self.assertEqual(loan.status, 'rejected')

    def test_member_cannot_approve_loan(self):
        """Regular member cannot approve loans"""
        loan = LoanApplication.objects.create(
            applicant=self.admin,
            chama=self.chama,
            amount_requested=2000,
            purpose='Test',
            status='pending'
        )
        self.client.force_authenticate(user=self.member)
        response = self.client.post(f'/api/loans/{loan.id}/review/', {
            'action': 'approve',
            'amount_approved': 2000
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)