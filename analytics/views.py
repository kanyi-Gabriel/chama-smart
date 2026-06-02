from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .ml_scorer import get_credit_score, update_member_credit_score
from .feature_engineering import extract_member_features
from contributions.models import Contribution
from loans.models import LoanApplication
from chamas.models import Membership
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta


class MyCreditScoreView(APIView):
    """Member views their own credit score and what drives it"""
    permission_classes = [IsAuthenticated]

    def get(self, request, chama_id=None):
        chama = None
        if chama_id:
            from chamas.models import Chama
            try:
                chama = Chama.objects.get(id=chama_id)
            except Chama.DoesNotExist:
                return Response({'error': 'Chama not found'}, status=404)

        result = get_credit_score(request.user, chama)

        return Response({
            'credit_score': result['score'],
            'recommendation': result['recommendation'],
            'risk_level': result['risk_level'],
            'score_breakdown': {
                'on_time_payment_rate': f"{result['features']['on_time_rate'] * 100:.1f}%",
                'contribution_completion_rate': f"{result['features']['completed_rate'] * 100:.1f}%",
                'loan_repayment_rate': f"{result['features']['loan_repayment_rate'] * 100:.1f}%",
                'months_active': result['features']['months_active'],
                'defaulted_loans': result['features']['defaulted_loans'],
            },
            'how_to_improve': _get_improvement_tips(result['features'])
        })


def _get_improvement_tips(features):
    tips = []
    if features['on_time_rate'] < 0.8:
        tips.append("Pay contributions on time — this is the biggest factor in your score")
    if features['completed_rate'] < 0.9:
        tips.append("Make sure to complete all your scheduled contributions")
    if features['defaulted_loans'] > 0:
        tips.append("Repay any outstanding loans — defaults heavily impact your score")
    if features['months_active'] < 6:
        tips.append("Stay active — your score improves with longer membership history")
    if not tips:
        tips.append("Great standing! Keep up the consistent contributions")
    return tips


class ChamaAnalyticsView(APIView):
    """Admin view - chama-wide financial analytics"""
    permission_classes = [IsAuthenticated]

    def get(self, request, chama_id):
        try:
            Membership.objects.get(
                user=request.user,
                chama_id=chama_id,
                is_active=True
            )
        except Membership.DoesNotExist:
            return Response({'error': 'Access denied'}, status=403)

        contributions = Contribution.objects.filter(chama_id=chama_id)
        total_collected = contributions.filter(
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0

        loans = LoanApplication.objects.filter(chama_id=chama_id)
        total_loaned = loans.filter(
            status__in=['approved', 'disbursed', 'repaid']
        ).aggregate(total=Sum('amount_approved'))['total'] or 0

        memberships = Membership.objects.filter(
            chama_id=chama_id, is_active=True
        ).select_related('user')

        member_scores = [
            {
                'name': m.user.get_full_name() or m.user.phone_number,
                'credit_score': m.credit_score,
                'risk_level': 'low' if m.credit_score >= 70
                              else 'medium' if m.credit_score >= 50
                              else 'high'
            }
            for m in memberships
        ]

        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_contributions = contributions.filter(
            transaction_date__gte=thirty_days_ago,
            status='completed'
        ).count()

        return Response({
            'total_collected': float(total_collected),
            'total_loaned': float(total_loaned),
            'net_savings': float(total_collected - total_loaned),
            'total_members': memberships.count(),
            'recent_contributions_30days': recent_contributions,
            'member_credit_scores': member_scores,
            'health_score': _chama_health_score(
                total_collected, total_loaned, memberships
            )
        })


def _chama_health_score(collected, loaned, memberships):
    if collected == 0:
        return 'new'
    loan_ratio = float(loaned) / float(collected) if collected > 0 else 0
    avg_credit = sum(
        m.credit_score for m in memberships
    ) / max(memberships.count(), 1)

    if loan_ratio < 0.5 and avg_credit >= 65:
        return 'excellent'
    elif loan_ratio < 0.7 and avg_credit >= 50:
        return 'good'
    else:
        return 'needs_attention'