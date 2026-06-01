from rest_framework import serializers
from .models import Chama, Membership
from accounts.serializers import UserProfileSerializer


class ChamaSerializer(serializers.ModelSerializer):
    created_by = UserProfileSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Chama
        fields = ['id', 'name', 'description', 'contribution_amount',
                  'frequency', 'created_by', 'created_at', 'is_active',
                  'max_members', 'member_count']
        read_only_fields = ['id', 'created_by', 'created_at']

    def get_member_count(self, obj):
        return obj.memberships.filter(is_active=True).count()


class MembershipSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    chama = ChamaSerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ['id', 'user', 'chama', 'role', 'date_joined',
                  'is_active', 'credit_score']
        read_only_fields = ['id', 'user', 'date_joined', 'credit_score']