from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Chama, Membership
from .serializers import ChamaSerializer, MembershipSerializer


class ChamaListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChamaSerializer

    def get_queryset(self):
        return Chama.objects.filter(is_active=True)

    def perform_create(self, serializer):
        chama = serializer.save(created_by=self.request.user)
        Membership.objects.create(
            user=self.request.user,
            chama=chama,
            role='chairperson',
            status='active'  # creator is immediately active
        )


class ChamaDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChamaSerializer
    queryset = Chama.objects.all()


class JoinChamaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, chama_id):
        try:
            chama = Chama.objects.get(id=chama_id, is_active=True)
        except Chama.DoesNotExist:
            return Response({'error': 'Chama not found'}, status=status.HTTP_404_NOT_FOUND)

        if Membership.objects.filter(user=request.user, chama=chama).exists():
            return Response({'error': 'You already have a membership request for this chama'}, status=status.HTTP_400_BAD_REQUEST)

        if chama.memberships.filter(is_active=True, status='active').count() >= chama.max_members:
            return Response({'error': 'This chama is full'}, status=status.HTTP_400_BAD_REQUEST)

        membership = Membership.objects.create(
            user=request.user,
            chama=chama,
            role='member',
            status='pending'  # requires admin approval
        )

        return Response({
            'message': f'Request to join {chama.name} submitted. Waiting for admin approval.',
            'membership': MembershipSerializer(membership).data
        }, status=status.HTTP_201_CREATED)

class MyChamasView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MembershipSerializer

    def get_queryset(self):
        return Membership.objects.filter(
            user=self.request.user,
            is_active=True,
            status='active'  # only show approved memberships
        ).select_related('chama', 'user')
    

class PendingMembersView(generics.ListAPIView):
    """Admin sees pending membership requests"""
    permission_classes = [IsAuthenticated]
    serializer_class = MembershipSerializer

    def get_queryset(self):
        chama_id = self.kwargs['chama_id']
        # Verify requester is admin
        try:
            Membership.objects.get(
                user=self.request.user,
                chama_id=chama_id,
                role__in=['chairperson', 'treasurer'],
                is_active=True,
                status='active'
            )
        except Membership.DoesNotExist:
            return Membership.objects.none()

        return Membership.objects.filter(
            chama_id=chama_id,
            status='pending'
        ).select_related('user')


class ReviewMembershipView(APIView):
    """Admin approves or rejects a membership request"""
    permission_classes = [IsAuthenticated]

    def post(self, request, membership_id):
        try:
            membership = Membership.objects.get(id=membership_id)
        except Membership.DoesNotExist:
            return Response({'error': 'Membership not found'}, status=status.HTTP_404_NOT_FOUND)

        # Verify admin
        try:
            Membership.objects.get(
                user=request.user,
                chama=membership.chama,
                role__in=['chairperson', 'treasurer'],
                status='active'
            )
        except Membership.DoesNotExist:
            return Response({'error': 'Only admins can approve memberships'}, status=status.HTTP_403_FORBIDDEN)

        action = request.data.get('action')
        if action == 'approve':
            membership.status = 'active'
            membership.save()
            return Response({'message': f'{membership.user.get_full_name()} approved successfully'})
        elif action == 'reject':
            membership.status = 'rejected'
            membership.save()
            return Response({'message': f'Membership rejected'})
        else:
            return Response({'error': 'Action must be approve or reject'}, status=status.HTTP_400_BAD_REQUEST)