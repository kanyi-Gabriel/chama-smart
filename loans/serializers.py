from rest_framework import serializers
from .models import LoanApplication, LoanRepayment
from accounts.serializers import UserProfileSerializer


class LoanApplicationSerializer(serializers.ModelSerializer):
    applicant = UserProfileSerializer(read_only=True)
    chama_name = serializers.CharField(source='chama.name', read_only=True)
    total_repayable = serializers.SerializerMethodField()

    class Meta:
        model = LoanApplication
        fields = ['id', 'applicant', 'chama', 'chama_name', 'amount_requested',
                  'amount_approved', 'purpose', 'status', 'ml_credit_score',
                  'ml_recommendation', 'applied_at', 'reviewed_at', 'reviewed_by',
                  'repayment_period_months', 'interest_rate', 'total_repayable']
        read_only_fields = ['id', 'applicant', 'chama', 'status', 'ml_credit_score',
                           'ml_recommendation', 'applied_at', 'reviewed_at',
                           'reviewed_by', 'amount_approved']

    def get_total_repayable(self, obj):
        if obj.amount_approved:
            interest = obj.amount_approved * (obj.interest_rate / 100)
            return float(obj.amount_approved + interest)
        return None


class LoanRepaymentSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.get_full_name', read_only=True)

    class Meta:
        model = LoanRepayment
        fields = ['id', 'loan', 'member', 'member_name', 'amount',
                  'mpesa_reference', 'status', 'paid_at']
        read_only_fields = ['id', 'member', 'status', 'paid_at']


class LoanApprovalSerializer(serializers.Serializer):
    """Used by admin to approve or reject a loan"""
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    amount_approved = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )
    notes = serializers.CharField(required=False, allow_blank=True)