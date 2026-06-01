from rest_framework import serializers
from .models import Contribution, Penalty
from chamas.serializers import ChamaSerializer


class ContributionSerializer(serializers.ModelSerializer):
    chama_name = serializers.CharField(source='chama.name', read_only=True)
    member_name = serializers.CharField(source='member.get_full_name', read_only=True)

    class Meta:
        model = Contribution
        fields = ['id', 'member', 'member_name', 'chama', 'chama_name',
                  'amount', 'status', 'mpesa_reference', 'transaction_date',
                  'due_date', 'is_late', 'penalty_amount', 'notes']
        read_only_fields = ['id', 'member', 'status', 'mpesa_reference',
                           'transaction_date', 'is_late', 'penalty_amount']


class PenaltySerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.get_full_name', read_only=True)

    class Meta:
        model = Penalty
        fields = ['id', 'member', 'member_name', 'chama', 'amount',
                  'reason', 'is_paid', 'created_at']
        read_only_fields = ['id', 'member', 'created_at']