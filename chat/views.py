from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Message
from chamas.models import Membership
from rest_framework import serializers


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    sender_phone = serializers.CharField(source='sender.phone_number', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'sender_name', 'sender_phone', 'content',
                  'message_type', 'is_pinned', 'timestamp']


class MessageListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer

    def get_queryset(self):
        chama_id = self.kwargs['chama_id']
        return Message.objects.filter(
            chama_id=chama_id
        ).select_related('sender').order_by('-timestamp')[:100]


class PinMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, chama_id, message_id):
        try:
            membership = Membership.objects.get(
                user=request.user,
                chama_id=chama_id,
                role__in=['chairperson', 'treasurer'],
                status='active'
            )
        except Membership.DoesNotExist:
            return Response({'error': 'Only admins can pin messages'}, status=403)

        try:
            message = Message.objects.get(id=message_id, chama_id=chama_id)
            message.is_pinned = not message.is_pinned
            message.save()
            return Response({'pinned': message.is_pinned})
        except Message.DoesNotExist:
            return Response({'error': 'Message not found'}, status=404)