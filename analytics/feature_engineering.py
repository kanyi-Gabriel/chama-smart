from django.utils import timezone
from django.db.models import Count, Avg
from contributions.models import Contribution
from loans.models import LoanApplication, LoanRepayment
from chamas.models import Membership
import pandas as pd
from datetime import timedelta


def extract_member_features(user, chama=None):
    """
    Extracts behavioral features for a member.
    These features feed directly into the credit scoring model.

    Args:
        user: User object
        chama: Optional - score within specific chama, or across all

    Returns:
        dict of features
    """
    # Filter contributions
    contributions = Contribution.objects.filter(member=user)
    if chama:
        contributions = contributions.filter(chama=chama)

    total = contributions.count()

    if total == 0:
        # Brand new member — return neutral features
        return {
            'total_contributions': 0,
            'on_time_rate': 0.5,
            'late_rate': 0.0,
            'completed_rate': 0.0,
            'avg_penalty_amount': 0.0,
            'penalty_frequency': 0.0,
            'months_active': 0,
            'loan_repayment_rate': 0.5,
            'active_loans': 0,
            'defaulted_loans': 0,
        }

    completed = contributions.filter(status='completed').count()
    late = contributions.filter(is_late=True).count()
    on_time = completed - late

    # Penalty stats
    penalties = contributions.filter(penalty_amount__gt=0)
    avg_penalty = penalties.aggregate(
        avg=Avg('penalty_amount')
    )['avg'] or 0.0

    # How long has this member been active?
    first_contribution = contributions.order_by('transaction_date').first()
    if first_contribution:
        months_active = max(1, (
            timezone.now() - first_contribution.transaction_date
        ).days // 30)
    else:
        months_active = 0

    # Loan repayment behavior
    loans = LoanApplication.objects.filter(applicant=user)
    if chama:
        loans = loans.filter(chama=chama)

    total_loans = loans.count()
    repaid_loans = loans.filter(status='repaid').count()
    defaulted_loans = loans.filter(status='defaulted').count()
    active_loans = loans.filter(status__in=['approved', 'disbursed']).count()

    loan_repayment_rate = (
        repaid_loans / total_loans if total_loans > 0 else 0.5
    )

    return {
        'total_contributions': total,
        'on_time_rate': on_time / completed if completed > 0 else 0.5,
        'late_rate': late / total if total > 0 else 0.0,
        'completed_rate': completed / total if total > 0 else 0.0,
        'avg_penalty_amount': float(avg_penalty),
        'penalty_frequency': late / months_active if months_active > 0 else 0.0,
        'months_active': months_active,
        'loan_repayment_rate': loan_repayment_rate,
        'active_loans': active_loans,
        'defaulted_loans': defaulted_loans,
    }