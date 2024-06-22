"""
Serializers for files APIs
"""
from rest_framework import serializers
from core.models import (
    FileProduction,
    Project,
    CommentFileProduction,
    Task,
    NotificationTask
)
from department.serializers import DepartmentSerializer
from user.serializers import UserNestedSerializer


def validate_file_extension(file_extension):
    allowed_extensions = ['pdf', 'dxf', 'xlsx', 'xls',
                          'txt', 'png', 'jpg', 'jpeg',
                          'rar', 'zip', 'doc', 'docx',
                          'igs', 'step', 'stp', 'stl']
    if file_extension in allowed_extensions:
        return True
    else:
        return False


class FilesUploadSerializer(serializers.ModelSerializer):
    """Serializer for upload file"""
    file = serializers.ListField(
        child=serializers.FileField(
            max_length=10000000000000,
            allow_empty_file=False,
            use_url=False
        ))

    class Meta:
        model = FileProduction
        fields = '__all__'

        extra_kwargs = {
            'name': {'required': False},
        }

    def create(self, validated_data):
        project = validated_data['project']
        user = validated_data['user']
        file = validated_data.pop('file')
        file_list = []
        for file in file:
            file_name_str = str(file).lower()
            file_split = file_name_str.split('.')
            file_extension = file_split[-1]
            if validate_file_extension(file_extension):
                file_obj = FileProduction.objects.create(
                    file=file, project=project, user=user,
                    name=file.name
                )
                fileurl = f'{file_obj.name}'
                file_list.append(fileurl)
            else:
                raise serializers.ValidationError('Wrong file format')
        return file_list


class FileProductionManageSerializer(serializers.ModelSerializer):
    """Serializer for manage file"""

    class Meta:
        model = FileProduction
        fields = ['id', 'name', 'file', 'tasks', 'comments']
        read_only_fields = ['id']


class FileProductionUncheckFlagSerializer(serializers.ModelSerializer):
    """Serializer for uncheck file flag"""

    class Meta:
        model = FileProduction
        fields = ['id', 'new']
        read_only_fields = ['id']


class CommentFileDisplaySerializer(serializers.ModelSerializer):
    """Serializer for comment file"""

    class Meta:
        model = CommentFileProduction
        fields = ['id', 'user', 'text', 'file', 'date_posted', 'read']
        read_only_fields = ['id', 'user', 'date_posted']

    def to_representation(self, instance):
        response = super().to_representation(instance)
        first_name = UserNestedSerializer(instance.user).data['first_name']
        last_name = UserNestedSerializer(instance.user).data['last_name']
        response['user'] = {
            'id': UserNestedSerializer(instance.user).data['id'],
            'name': first_name[0].upper() + '. ' + last_name
        }
        response['task'] = {
            'id': FileProductionManageSerializer(instance.file).data['id']
        }
        return response


class CommentFileProductionManageSerializer(serializers.ModelSerializer):
    """Serializer Manage for comment file"""

    class Meta:
        model = CommentFileProduction
        fields = ['id', 'user', 'file', 'text']
        read_only_fields = ['id']


class TaskUpdateSerializer(serializers.ModelSerializer):
    """Serializer Manage for comment file"""

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['id', 'project', 'department', 'file']


class TaskManageSerializer(serializers.ModelSerializer):
    """Serializer for manage tasks logic"""

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['id']


class TaskManageSerializerWithDepartment(serializers.ModelSerializer):
    """Serializer for manage tasks logic with department"""
    department = DepartmentSerializer(many=False)

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['id']


class TaskWebSocketNotificationSerializer(serializers.ModelSerializer):
    """Serializer for task websocket"""

    class Meta:
        model = NotificationTask
        fields = ['id', 'user', 'department', 'file', 'content']
        read_only_fields = ['id']


class FileSerializerWithDepartment(serializers.ModelSerializer):
    """Serializer for file in project with department"""
    #comments = CommentFileDisplaySerializer(many=True)
    tasks = TaskManageSerializerWithDepartment(many=True)

    class Meta:
        model = FileProduction
        fields = [
            'id', 'name', 'file',
            'project', 'tasks', 'new'
        ]
        read_only_fields = ['id']


class FileProductionProjectSerializer(serializers.ModelSerializer):
    """Serializer for file production in project"""
    comments = CommentFileDisplaySerializer(many=True)
    tasks = TaskManageSerializer(many=True)

    class Meta:
        model = FileProduction
        fields = [
            'id', 'name', 'file', 'comments',
            'project', 'tasks', 'new'
        ]
        read_only_fields = ['id']

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['dep_id'] = []
        for task in response['tasks']:
            response['dep_id'].append(task['department'])
        return response


class ProjectFileSerializer(serializers.ModelSerializer):
    """Serializer for project"""

    class Meta:
        model = Project
        fields = ['id', 'manager', 'number']

    def to_representation(self, instance):
        response = super().to_representation(instance)
        first_name = UserNestedSerializer(instance.manager).data['first_name']
        last_name = UserNestedSerializer(instance.manager).data['last_name']
        manager = first_name[0].upper() + '. ' + last_name
        response['manager'] = manager
        return response


class TaskCalendarSerializer(serializers.ModelSerializer):
    """Serializer for task user in calendar"""

    project = ProjectFileSerializer(many=False)
    department = DepartmentSerializer(many=False)
    file = FileProductionManageSerializer(many=False)

    class Meta:
        model = Task
        fields = [
            'id', 'file', 'department',
            'project', 'users', 'planned_start_date',
            'planned_end_date', 'start', 'paused', 'end'
        ]
        read_only_fields = ['id']


class TaskSelfSerializer(serializers.ModelSerializer):
    """Serializer for manage tasks logic"""
    department = DepartmentSerializer(many=False)
    users = UserNestedSerializer(many=True)

    class Meta:
        model = Task
        exclude = ['test', 'previous_task', 'next_task', 'file']
        read_only_fields = ['id']


class FileProductionDepartmentSerializer(serializers.ModelSerializer):
    """Serializer for manage file"""
    comments = CommentFileDisplaySerializer(many=True)

    class Meta:
        model = FileProduction
        fields = ['id', 'name', 'file', 'tasks', 'comments']
        read_only_fields = ['id']


class TaskDepartmentSerializer(serializers.ModelSerializer):
    """Serializer for file in department"""

    file = FileProductionDepartmentSerializer(many=False)
    next_task = TaskSelfSerializer(many=False)
    previous_task = TaskSelfSerializer(many=False)
    manager = UserNestedSerializer(many=False)

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['id']

    def to_representation(self, instance):
        response = super().to_representation(instance)
        return response


class NotificationTaskSerializer(serializers.ModelSerializer):
    """Serializer for NotificationTask"""

    department = DepartmentSerializer(many=False)

    class Meta:
        model = NotificationTask
        fields = '__all__'
        read_only_fields = ['id']
