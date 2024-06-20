import json

from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser


class ProjectConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        if user is not AnonymousUser():
            await self.channel_layer.group_add(
                f'user_project_notification_{user.id}',
                self.channel_name
            )
            await self.accept()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json['type']
        message = text_data_json

        if message_type == 'project_notification':
            await self.project_notification(message)

    async def project_notification(self, event):
        message = event['message']
        user = self.scope['user']

        if user is not AnonymousUser():
            await self.send(text_data=json.dumps({
                'message': message,
            }))


class ProjectBoardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        if user is not AnonymousUser():
            await self.channel_layer.group_add(
                f'user_project_data_{user.id}',
                self.channel_name
            )
            await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message_type = text_data_json['type']
        message = text_data_json

        if message_type == 'project_data':
            await self.project_data(message)

    async def project_data(self, event):
        message = event['message']
        user = self.scope['user']

        if user is not AnonymousUser():
            await self.send(text_data=json.dumps({
                'message': message,
            }))
