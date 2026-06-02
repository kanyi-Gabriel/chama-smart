from django.test import TestCase
from accounts.models import User
from chamas.models import Chama, Membership
from analytics.ml_scorer import get_credit_score, rules_based_score
from analytics.feature_engineering import extract_member_features


class CreditScoringTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='0712300001',
            phone_number='0712300001',
            password='StrongPass123!'
        )
        self.chama = Chama.objects.create(
            name='Score Test Chama',
            contribution_amount=1000,
            frequency='monthly',
            created_by=self.user
        )
        Membership.objects.create(
            user=self.user,
            chama=self.chama,
            role='admin'
        )

    def test_new_member_gets_neutral_score(self):
        """Brand new member with no history gets neutral score"""
        result = get_credit_score(self.user, self.chama)
        self.assertGreater(result['score'], 0)
        self.assertLessEqual(result['score'], 100)

    def test_score_within_valid_range(self):
        """Credit score always stays between 0 and 100"""
        result = get_credit_score(self.user)
        self.assertGreaterEqual(result['score'], 0)
        self.assertLessEqual(result['score'], 100)

    def test_perfect_features_give_high_score(self):
        """Member with perfect payment history gets high score"""
        perfect_features = {
            'total_contributions': 12,
            'on_time_rate': 1.0,
            'late_rate': 0.0,
            'completed_rate': 1.0,
            'avg_penalty_amount': 0.0,
            'penalty_frequency': 0.0,
            'months_active': 12,
            'loan_repayment_rate': 1.0,
            'active_loans': 0,
            'defaulted_loans': 0,
        }
        score = rules_based_score(perfect_features)
        self.assertGreaterEqual(score, 80)

    def test_poor_features_give_low_score(self):
        """Member with defaults and late payments gets low score"""
        poor_features = {
            'total_contributions': 5,
            'on_time_rate': 0.2,
            'late_rate': 0.8,
            'completed_rate': 0.3,
            'avg_penalty_amount': 500.0,
            'penalty_frequency': 2.0,
            'months_active': 2,
            'loan_repayment_rate': 0.0,
            'active_loans': 0,
            'defaulted_loans': 2,
        }
        score = rules_based_score(poor_features)
        self.assertLess(score, 30)

    def test_result_has_required_fields(self):
        """Score result always has all required fields"""
        result = get_credit_score(self.user)
        self.assertIn('score', result)
        self.assertIn('recommendation', result)
        self.assertIn('risk_level', result)
        self.assertIn('features', result)

    def test_recommendation_matches_score(self):
        """Recommendation correctly reflects the score"""
        result = get_credit_score(self.user)
        if result['score'] >= 70:
            self.assertEqual(result['recommendation'], 'approve')
        elif result['score'] >= 50:
            self.assertEqual(result['recommendation'], 'review')
        else:
            self.assertEqual(result['recommendation'], 'reject')