import math

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from core.models import (
    Project,
    Task,
    FileProduction,
    Department,
    User,
    CommentFileProduction
)
from department.serializers import DepartmentSerializer
from django.core.paginator import Paginator
from fileproduction import serializers
from project.serializers import ProjectProgressSerializer
from rest_framework import status
from rest_framework.response import Response
from user.serializers import UserWebsocketSerializer


def get_file_project_data(file_id):
    """Return file in project data dictionary"""
    file = FileProduction.objects.filter(id=file_id).first()
    serializer_file = serializers.FileSerializerWithDepartment(file, many=False)
    return serializer_file.data


def uncheck_new_file_flag(file_id):
    """uncheck new file flag just change value True to False"""

    file = FileProduction.objects.filter(id=file_id).first()
    update_data = {
        "new": False
    }
    serializer_file = serializers.FileProductionUncheckFlagSerializer(file, data=update_data)
    if serializer_file.is_valid():
        serializer_file.save()


def get_queue_status(queue_status):
    if queue_status == 'Active':
        status_filter = True
    elif queue_status == 'Completed':
        status_filter = False
    else:
        status_filter = None

    if status_filter is None:
        return None

    return status_filter


def paginate(page_size, page_number, query):
    paginator = Paginator(query, page_size)
    page_obj = paginator.get_page(page_number)
    serializer = serializers.TaskDepartmentSerializer(
        page_obj,
        many=True
    )
    total_items = paginator.count
    max_pages = math.ceil(total_items / int(page_size))
    ser_data = serializer.data if max_pages >= int(page_number) else {}
    data = {
        'data': ser_data,
        'totalItems': total_items
    }
    return data


def project_progress(project_id):
    """Calculate project progress"""
    total_tasks = Task.objects.filter(project=project_id).count()
    completed_tasks = Task.objects.filter(project=project_id, end=True).count()
    project = Project.objects.get(id=project_id)

    try:
        progress_percentage = (completed_tasks / total_tasks) * 100
    except ZeroDivisionError:
        progress_percentage = 0

    progress_data = {'progress': int(progress_percentage)}
    if progress_percentage == 100:
        progress_data['status'] = 'Completed'
    elif progress_percentage >= 0:
        progress_data['status'] = 'Started'

    serializer = ProjectProgressSerializer(project, data=progress_data)
    if serializer.is_valid():
        serializer.save()


def task_permission_update(task_id, permission):
    """get task to update after POST, UPDATE, PATCH or DELETE task"""
    if not permission:
        update_task = Task.objects.get(id=task_id)
        update_task.permission = False
        update_task.start = False
        update_task.paused = False
        update_task.end = False
        update_task.save()
    else:
        update_task = Task.objects.get(id=task_id)
        update_task.permission = True
        update_task.save()


def task_permission_perform_create(validated_data):
    """updating task permission after POST, in perform_create"""
    file_id = validated_data['file'].id
    file_tasks = get_file_project_data(file_id)

    if not file_tasks['tasks']:
        validated_data['permission'] = True
    else:
        first_task = file_tasks['tasks'][0]
        remaining_tasks = file_tasks['tasks'][1:]
        if validated_data['department'].order < first_task['department']['order']:
            remaining_tasks.append(first_task)
            validated_data['permission'] = True
            for task in remaining_tasks:
                task_permission_update(task['id'], False)
        else:
            task_permission_update(first_task['id'], True)
            for task in remaining_tasks:
                task_permission_update(task['id'], False)


def task_in_create(response, file):
    """
        Updating next_task and previous_task and
        calculate project progress in create
    """
    current_task_id = response.data['id']
    current_index = next((i for i, task in enumerate(file['tasks']) if task['id'] == current_task_id), None)
    current_task = Task.objects.get(id=current_task_id)

    if current_index > 0:
        previous_task = Task.objects.get(id=file['tasks'][current_index - 1]['id'])
        current_task.previous_task = previous_task
        previous_task.next_task = current_task
        previous_task.save()

    if current_index < len(file['tasks']) - 1:
        next_task = Task.objects.get(id=file['tasks'][current_index + 1]['id'])
        current_task.next_task = next_task
        next_task.previous_task = current_task
        next_task.save()
    current_task.save()
    project_progress(current_task.project.id)
    return current_task


def task_in_destroy(tasks, task_index, current_task):
    """
        Updating next_task and previous_task and
        calculate project progress in destroy
    """
    if task_index == 0:
        if len(tasks) == 1:
            return
        next_task = Task.objects.get(id=tasks[1]['id'])
        next_task.permission = True
        next_task.previous_task = None
        next_task.save()
    elif task_index == len(tasks) - 1:
        previous_task = Task.objects.get(id=tasks[task_index - 1]['id'])
        previous_task.next_task = None
        previous_task.save()
    else:
        next_task = Task.objects.get(id=tasks[task_index + 1]['id'])
        previous_task = Task.objects.get(id=tasks[task_index - 1]['id'])
        next_task.previous_task = previous_task
        previous_task.next_task = next_task
        if previous_task.end and not next_task.permission:
            next_task.permission = True
        next_task.save()
        previous_task.save()


def task_in_update(task_obj, request_data):
    """
        Update task and calculate project progress in update
    """
    file = get_file_project_data(task_obj.file.id)
    tasks = file.get('tasks', [])
    task_ids = [task['id'] for task in tasks]
    task_index = task_ids.index(task_obj.id)
    if task_index == 0 and task_obj.permission:
        if len(tasks) == 1:
            return
        try:
            if request_data['end']:
                update_next_task_permission(tasks[1]['id'])
                return
            task_ids.remove(task_ids[0])
            for task_id in task_ids:
                reset_tasks(task_id)
            return
        except KeyError:
            return
    elif task_index == len(tasks) - 1 and task_obj.permission:
        return
    else:
        try:
            if request_data['end']:
                update_next_task_permission(tasks[task_index + 1]['id'])
                return
            for task_id in task_ids[task_index + 1:]:
                reset_tasks(task_id)
            return
        except KeyError:
            return


def update_next_task_permission(task_id):
    next_task = Task.objects.get(id=task_id)
    next_task.permission = True
    next_task.save()


def reset_tasks(task_id):
    task = Task.objects.get(id=task_id)
    task.permission = False
    task.start = False
    task.paused = False
    task.end = False
    task.save()


def tasks_dep_admin(params):
    dep_id = params.get('dep_id')
    page_size = params.get('page_size')
    page_number = params.get('page_number')
    status_param = params.get('status')

    status_filter = get_queue_status(status_param)

    if status_filter is None:
        return Response(
            {'message': 'There is no such file status'},
            status=status.HTTP_404_NOT_FOUND
        )
    else:
        department_query = Department.objects.get(id=int(dep_id))
        serializer_dep = DepartmentSerializer(department_query, many=False)
        department_data = serializer_dep.data

        if status_filter:
            task_query = Task.objects.filter(
                department=dep_id,
                end=True
            )
        else:
            task_query = Task.objects.filter(
                department=dep_id,
                end=False
            )

        tasks = paginate(page_size, page_number, task_query)
        data = {
            'department': department_data,
            'tasks': tasks
        }
        return data


def files_dep_auth(params, user_id):
    dep_id = params.get('dep_id')
    page_size = params.get('page_size')
    page_number = params.get('page_number')
    status_param = params.get('status')

    status_filter = get_queue_status(status_param)

    if status_filter is None:
        return Response(
            {'message': 'There is no such file status'},
            status=status.HTTP_404_NOT_FOUND
        )
    else:
        query_dep = Department.objects.get(id=int(dep_id))
        serializer_dep = DepartmentSerializer(query_dep, many=False)
        department = serializer_dep.data

        query_file = FileProduction.objects.filter(
            tasks__department=int(dep_id),
            tasks__users__in=[user_id],
            tasks__end=False
        )
        files = paginate(page_size, page_number, dep_id, query_file)
        data = {
            'department': department,
            'files': files
        }
        return data


def search_files(params):
    queue_status = params.get('status')
    search_phase = params.get('search')
    dep_id = params.get('dep_id')
    status_filter = get_queue_status(queue_status)

    if status_filter is None:
        return Response({'message': 'There is no such file status \
                          or you do not have permission'},
                        status=status.HTTP_404_NOT_FOUND)

    query_dep = Department.objects.get(id=int(dep_id))
    serializer_dep = DepartmentSerializer(query_dep, many=False)
    department = serializer_dep.data

    query_file = FileProduction.objects.filter(
        name__icontains=search_phase,
        tasks__department=int(dep_id),
        tasks__end=not status_filter
    )

    context = {'dep_id': int(dep_id)}
    serializer_file = serializers.TaskDepartmentSerializer(
        query_file,
        many=True,
        context=context
    )
    files = serializer_file.data
    data = {
        'department': department,
        'files': files
    }
    return data


def send_message(group, message_type, message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            'type': message_type,
            'message': message,
        }
    )


def notification_ws(data):
    department = Department.objects.get(id=data['department'])
    file = FileProduction.objects.get(id=data['file'])
    admin_user_query = User.objects.filter(role="Admin")
    employee_user_query = User.objects.filter(role="Employee", departments__in=[data['department']])
    users_union = admin_user_query.union(employee_user_query)
    all_users = UserWebsocketSerializer(users_union, many=True)
    users = all_users.data
    content = f'New Task ({file}) appeared in {department}'

    for user in users:
        notification = {
            "user": user["id"],
            "department": department.id,
            "file": file.id,
            "content": content
        }
        notification_serializer = serializers.TaskWebSocketNotificationSerializer(
            data=notification,
            many=False
        )
        if notification_serializer.is_valid():
            notification_serializer.save()
            message_type = 'task_noti'
            group = f'user_task_noti_{user['id']}'
            message = {
                'notification': notification_serializer.data,
                'task': data
            }
            send_message(group, message_type, message)


def task(file_id, users, destiny, where):
    """Prepare data for task in websocket"""

    file_query = FileProduction.objects.get(id=file_id)
    file_serializer = serializers.FileProductionProjectSerializer(file_query, many=False)
    file_data = file_serializer.data
    project_progress(file_data['project'])

    project_query = Project.objects.get(id=file_data['project'])
    project_serializer = ProjectProgressSerializer(project_query, many=False)
    project_data = project_serializer.data

    message = {
        'file': file_data,
        'project': project_data,
        'dep_id': file_data['dep_id'],
        'type': where
    }
    for user in users:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_file_modify_{destiny}_{user.id}',
            {
                'type': f'task_modify_{destiny}',
                'message': message,
            }
        )


def comment(comment_id, users, destiny, where):
    comment = CommentFileProduction.objects.get(id=comment_id)
    comment_ser = serializers.CommentFileDisplaySerializer(
        comment,
        many=False
    )
    comment_data = comment_ser.data
    message = {
        'comment': comment_data,
        'type': destiny,
    }
    for user in users:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_file_modify_{where}_{user.id}',
            {
                'type': f'task_modify_{where}',
                'message': message,
            }
        )


def update_task_project_ws(data, destiny):
    """Refresh task for file and progress for project in project view"""
    users = User.objects.filter(role='Admin')
    if destiny == 'task':
        task(data, users, 'project', destiny)

    elif destiny == 'comment_add' or destiny == 'comment_delete':
        comment(data, users, destiny, 'project')


def update_task_department_ws(data, destiny):
    """Refresh task for file in department view"""

    users = User.objects.all()

    if destiny == 'task':
        query = FileProduction.objects.get(id=data['id'])
        try:
            serializer_file = serializers.TaskDepartmentSerializer(
                query
            )
            file_data = serializer_file.data
            file_data['project'] = serializer_file.data['project']['id']
            task(file_data, users, 'department')
        except IndexError:
            pass

    elif destiny == 'comment_add' or destiny == 'comment_delete':
        comment(data, users, destiny, 'department')

    elif destiny == 'file_delete':
        pass
        # file_delete(data, users, 'department')
