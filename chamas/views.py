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
        # Save chama with current user as creator
        chama = serializer.save(created_by=self.request.user)
        # Automatically make creator an admin member
        Membership.objects.create(
            user=self.request.user,
            chama=chama,
            role='admin'
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

        # Check if already a member
        if Membership.objects.filter(user=request.user, chama=chama).exists():
            return Response({'error': 'You are already a member of this chama'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if chama is full
        if chama.memberships.filter(is_active=True).count() >= chama.max_members:
            return Response({'error': 'This chama is full'}, status=status.HTTP_400_BAD_REQUEST)

        membership = Membership.objects.create(
            user=request.user,
            chama=chama,
            role='member'
        )

        return Response({
            'message': f'Successfully joined {chama.name}',
            'membership': MembershipSerializer(membership).data
        }, status=status.HTTP_201_CREATED)


class MyChamasView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MembershipSerializer

    def get_queryset(self):
        return Membership.objects.filter(
            user=self.request.user,
            is_active=True
        ).select_related('chama', 'user')