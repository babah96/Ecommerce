import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Notification
from .serializers import NotificationSerializer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        if user.is_anonymous:
            await self.close()
        else:
            self.group_name = f'user_{user.id}'
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        # simple echo or ping handler
        await self.send(text_data=json.dumps({'message':'pong'}))

    async def send_notification(self, event):
        # event['notification'] is expected to be serialized data
        await self.send(text_data=json.dumps(event['notification']))

# helper to push notification from anywhere in sync code
@database_sync_to_async
def create_notification_and_broadcast(user, message, channel_layer):
    notif = Notification.objects.create(user=user, message=message)
    serializer = NotificationSerializer(notif)
    import asyncio
    # dispatch to group
    async def _send():
        await channel_layer.group_send(f'user_{user.id}', {
            'type':'send_notification',
            'notification': serializer.data,
        })
    asyncio.create_task(_send())