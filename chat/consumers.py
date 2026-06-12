import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.chama_id = self.scope['url_route']['kwargs']['chama_id']
        self.room_group_name = f'chat_{self.chama_id}'

        # Verify user is authenticated
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close()
            return

        # Verify user is member of this chama
        is_member = await self.check_membership(user, self.chama_id)
        if not is_member:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Send last 50 messages on connect
        messages = await self.get_recent_messages(self.chama_id)
        await self.send(text_data=json.dumps({
            'type': 'history',
            'messages': messages
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_content = data.get('message', '').strip()
        user = self.scope['user']

        if not message_content:
            return

        # Get user's role in chama
        role = await self.get_user_role(user, self.chama_id)
        message_type = 'announcement' if role in ['chairperson', 'treasurer'] and data.get('is_announcement') else 'text'

        # Save message to database
        message = await self.save_message(
            user, self.chama_id, message_content, message_type
        )

        # Broadcast to all members in the room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'id': message['id'],
                    'sender': message['sender'],
                    'sender_role': role,
                    'content': message_content,
                    'message_type': message_type,
                    'timestamp': message['timestamp'],
                }
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message']
        }))

    @database_sync_to_async
    def check_membership(self, user, chama_id):
        from chamas.models import Membership
        return Membership.objects.filter(
            user=user,
            chama_id=chama_id,
            is_active=True,
            status='active'
        ).exists()

    @database_sync_to_async
    def get_user_role(self, user, chama_id):
        from chamas.models import Membership
        try:
            m = Membership.objects.get(
                user=user, chama_id=chama_id, is_active=True
            )
            return m.role
        except Exception:
            return 'member'

    @database_sync_to_async
    def save_message(self, user, chama_id, content, message_type):
        from .models import Message
        from chamas.models import Chama
        chama = Chama.objects.get(id=chama_id)
        msg = Message.objects.create(
            chama=chama,
            sender=user,
            content=content,
            message_type=message_type
        )
        return {
            'id': msg.id,
            'sender': user.get_full_name() or user.phone_number,
            'timestamp': msg.timestamp.strftime('%H:%M · %d %b'),
        }

    @database_sync_to_async
    def get_recent_messages(self, chama_id):
        from .models import Message
        messages = Message.objects.filter(
            chama_id=chama_id
        ).select_related('sender').order_by('-timestamp')[:50]

        return [
            {
                'id': m.id,
                'sender': m.sender.get_full_name() or m.sender.phone_number,
                'content': m.content,
                'message_type': m.message_type,
                'is_pinned': m.is_pinned,
                'timestamp': m.timestamp.strftime('%H:%M · %d %b'),
            }
            for m in reversed(list(messages))
        ]