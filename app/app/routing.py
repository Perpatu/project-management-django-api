from django.urls import re_path
from fileproduction import consumer as file_consumer
from project import consumer as project_consumer

websocket_urlpatterns = [
    re_path(r'ws/project/', project_consumer.ProjectConsumer.as_asgi()),
    re_path(r'ws/project-data/', project_consumer.ProjectBoardConsumer.as_asgi()),
    re_path(r'ws/task/', file_consumer.FileNotiConsumer.as_asgi()),
    re_path(r'ws/task-project/', file_consumer.FileProjectConsumer.as_asgi()),
    re_path(r'ws/file-department/', file_consumer.FileDepartmentConsumer.as_asgi()),
]
