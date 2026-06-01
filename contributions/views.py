from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Contribution, Penalty
from .serializers import ContributionSerializer, PenaltySerializer
from chamas.models import Chama, Membership
from payments.daraja import stk_push


class ContributionListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ContributionSerializer

    def get_queryset(self):
        return Contribution.objects.filter(
            member=self.request.user
        ).order_by('-transaction_date')


class ChamaContributionsView(generics.ListAPIView):
    """Admin view - all contributions for a specific chama"""
    permission_classes = [IsAuthenticated]
    serializer_class = ContributionSerializer

    def get_queryset(self):
        chama_id = self.kwargs['chama_id']
        return Contribution.objects.filter(
            chama_id=chama_id
        ).order_by('-transaction_date')


class MakeContributionView(APIView):
    """
    Triggers M-Pesa STK push for a member's contribution.
    Creates a pending contribution record first,
    then sends payment prompt to their phone.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, chama_id):
        # Verify member belongs to this chama
        try:
            membership = Membership.objects.get(
                user=request.user,
                chama_id=chama_id,
                is_active=True
            )
        except Membership.DoesNotExist:
            return Response(
                {'error': 'You are not a member of this chama'},
                status=status.HTTP_403_FORBIDDEN
            )

        chama = membership.chama

        # Check for pending contribution (don't double-charge)
        existing = Contribution.objects.filter(
            member=request.user,
            chama=chama,
            status='pending'
        ).first()

        if existing:
            return Response(
                {'error': 'You have a pending contribution. Please wait for it to complete.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create contribution record (pending)
        contribution = Contribution.objects.create(
            member=request.user,
            chama=chama,
            amount=chama.contribution_amount,
            status='pending',
            due_date=request.data.get('due_date')
        )

        # Format phone number for Daraja (0712... → 254712...)
        phone = request.user.phone_number
        if phone.startswith('0'):
            phone = '254' + phone[1:]

        # Trigger STK Push
        response = stk_push(
            phone_number=phone,
            amount=int(chama.contribution_amount),
            account_reference=f'CHAMA{chama.id}',
            description=f'{chama.name} contribution'
        )

        if response.get('ResponseCode') == '0':
            return Response({
                'message': 'Payment prompt sent to your phone. Enter your M-Pesa PIN to complete.',
                'contribution_id': contribution.id,
                'amount': str(chama.contribution_amount),
                'chama': chama.name
            })
        else:
            # STK push failed — delete the pending record
            contribution.delete()
            return Response(
                {'error': 'Failed to send payment prompt', 'details': response},
                status=status.HTTP_400_BAD_REQUEST
            )


class MyPenaltiesView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PenaltySerializer

    def get_queryset(self):
        return Penalty.objects.filter(
            member=self.request.user
        ).order_by('-created_at')