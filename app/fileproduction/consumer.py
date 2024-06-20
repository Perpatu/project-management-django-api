import json

from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser


class FileNotiConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']

        if user is not AnonymousUser():
            await self.channel_layer.group_add(
                f'user_task_noti_{user.id}',
                self.channel_name
            )
            await self.accept()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        message = text_data_json

        if message_type == 'task_noti':
            await self.task_noti(message)

    async def task_noti(self, event):
        message = event['message']
        user = self.scope['user']

        if user is not AnonymousUser():
            await self.send(text_data=json.dumps({
                'message': message,
            }))


class FileProjectConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']

        if user is not AnonymousUser():
            await self.channel_layer.group_add(
                f'user_file_modify_project_{user.id}',
                self.channel_name
            )
            await self.accept()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        message = text_data_json

        if message_type == 'task_modify_project':
            await self.task_modify_project(message)

    async def task_modify_project(self, event):
        message = event['message']
        user = self.scope['user']

        if user is not AnonymousUser():
            await self.send(text_data=json.dumps({
                'message': message,
            }))


class FileDepartmentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']

        if user is not AnonymousUser():
            await self.channel_layer.group_add(
                f'user_file_modify_department_{user.id}',
                self.channel_name
            )
            await self.accept()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        message = text_data_json

        if message_type == 'task_modify_department':
            await self.task_modify_department(message)

    async def task_modify_department(self, event):
        message = event['message']
        user = self.scope['user']

        if user is not AnonymousUser():
            await self.send(text_data=json.dumps({
                'message': message,
            }))
