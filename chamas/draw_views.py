import secrets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Chama, Membership, DrawSession, DrawParticipant
from accounts.models import User


class StartDrawView(APIView):
    """
    Admin starts a draw session.
    Server picks winner using cryptographic randomness.
    Frontend receives the winner and plays the wheel animation.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, chama_id):
        # Verify admin
        try:
            membership = Membership.objects.get(
                user=request.user,
                chama_id=chama_id,
                role__in=['admin', 'treasurer'],
                is_active=True
            )
        except Membership.DoesNotExist:
            return Response(
                {'error': 'Only admins can start a draw'},
                status=status.HTTP_403_FORBIDDEN
            )

        chama = membership.chama

        # Check no active draw already running
        if DrawSession.objects.filter(chama=chama, status='active').exists():
            return Response(
                {'error': 'A draw is already in progress for this chama'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get eligible members (active, haven't won this cycle)
        members = Membership.objects.filter(
            chama=chama,
            is_active=True
        ).select_related('user')

        if members.count() < 2:
            return Response(
                {'error': 'Need at least 2 members for a draw'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create draw session
        session = DrawSession.objects.create(
            chama=chama,
            started_by=request.user,
            status='active',
            prize_amount=chama.contribution_amount * members.count()
        )

        # Add all members as participants with random positions
        member_list = list(members)
        # Shuffle positions using cryptographic randomness
        positions = list(range(1, len(member_list) + 1))
        secrets.SystemRandom().shuffle(positions)

        participants = []
        for i, membership in enumerate(member_list):
            participants.append(DrawParticipant(
                session=session,
                member=membership.user,
                position=positions[i]
            ))
        DrawParticipant.objects.bulk_create(participants)

        # Pick winner using cryptographic randomness
        winner_membership = secrets.choice(member_list)
        winner = winner_membership.user

        # Save winner
        session.winner = winner
        session.status = 'completed'
        session.completed_at = timezone.now()
        session.save()

        # Build participant list for wheel animation
        all_participants = DrawParticipant.objects.filter(
            session=session
        ).order_by('position').select_related('member')

        wheel_segments = [
            {
                'position': p.position,
                'member_id': p.member.id,
                'name': p.member.get_full_name() or p.member.phone_number,
                'is_winner': p.member == winner
            }
            for p in all_participants
        ]

        return Response({
            'session_id': session.id,
            'winner': {
                'id': winner.id,
                'name': winner.get_full_name() or winner.phone_number,
                'phone': winner.phone_number,
            },
            'prize_amount': str(session.prize_amount),
            'wheel_segments': wheel_segments,
            'total_members': len(member_list),
            'message': f'🎉 {winner.get_full_name()} won KES {session.prize_amount}!'
        })


class DrawHistoryView(APIView):
    """Shows all past draws for a chama"""
    permission_classes = [IsAuthenticated]

    def get(self, request, chama_id):
        sessions = DrawSession.objects.filter(
            chama_id=chama_id,
            status='completed'
        ).select_related('winner', 'started_by').order_by('-started_at')

        history = [
            {
                'id': s.id,
                'winner': s.winner.get_full_name() if s.winner else 'Unknown',
                'prize_amount': str(s.prize_amount),
                'date': s.completed_at,
                'started_by': s.started_by.get_full_name() if s.started_by else 'Unknown'
            }
            for s in sessions
        ]

        return Response({'draw_history': history})