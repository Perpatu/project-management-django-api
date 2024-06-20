import math

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from core.models import (
    Project,
    User
)
from django.contrib.postgres.search import SearchVector, SearchRank
from django.core.paginator import Paginator
from django.db.models import Q
from project.serializers import (
    ProjectSerializer,
    NotificationProjectSerializer
)
from rest_framework import status
from rest_framework.response import Response


def paginate(page_size, page_number, query):
    """ Paginate a project data """

    paginator = Paginator(query, page_size)
    page_obj = paginator.get_page(page_number)
    serializer = ProjectSerializer(page_obj, many=True)
    total_items = paginator.count
    max_pages = math.ceil(total_items / int(page_size))
    data = {
        'data': serializer.data if max_pages >= int(page_number) else {},
        'totalItems': total_items
    }
    return data


def project_production_status(project_status):
    """ Returns status of production project """

    status_mapping = {
        'Active': ['Started', 'In design'],
        'My_Active': ['Started', 'In design'],
        'My_Completed': ['Completed'],
        'My_Suspended': ['Suspended'],
        'Suspended': ['Suspended'],
        'Completed': ['Completed'],
    }

    status_filter = status_mapping.get(project_status)

    if status_filter is None:
        return None

    return status_filter


def project_secretariat_status(project_status, user=None):
    """ Returns status of secretariat project """

    status_mapping = {
        'YES': ['YES', 'YES (LACK OF INVOICE)'],
        'NO': ['NO'],
    }

    status_filter = status_mapping.get(project_status)

    if status_filter is None:
        return None

    if user and not user.is_staff:
        status_filter = None

    return status_filter


def search_secretariat_projects(params, user):
    """ Returns data for secretariat projects filtered by search params. """

    project_status = params.get('status')
    search = params.get('search')
    status_filter = project_secretariat_status(project_status, user)

    if status_filter is None:
        info = {
            'message': 'There is no such project status '
                       'or you do not have permission'
        }
        return Response(info, status=status.HTTP_404_NOT_FOUND)

    queryset = Project.objects.filter(
        Q(invoiced__in=status_filter) &
        Q(secretariat=True) &
        (Q(number__icontains=search) |
         Q(name__icontains=search) |
         Q(order_number__icontains=search))
    )

    serializer = ProjectSerializer(queryset, many=True)
    return serializer.data


def search_projects(params, user):
    """ Returns data for production projects filtered by search params """

    status_params = params.get('status')
    search_query = params.get('search')
    project_status = project_production_status(status_params)

    if project_status is None:
        return None

    search_vector = SearchVector(
        'name', 'order_number',
        'client__name', 'manager__last_name'
    )
    if not status_params.startswith('My'):
        project = Project.objects.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query)
        ).filter(search__icontains=search_query, status__in=project_status)
    else:
        project = Project.objects.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query)
        ).filter(search__icontains=search_query, status__in=project_status, manager=user)

    page_size = params.get('page_size')
    page_number = params.get('page_number')
    data = paginate(page_size, page_number, project)
    return data


def filter_production_projects(queryset, params, user):
    """ Returns data for production projects filtered by project status """

    project_status = params.get('status')
    status_filter = project_production_status(project_status)
    if status_filter is None:
        return None

    if not project_status.startswith('My'):
        queryset = queryset.filter(status__in=status_filter)
    else:
        queryset = queryset.filter(manager=user, status__in=status_filter)

    page_size = params.get('page_size')
    page_number = params.get('page_number')
    data = paginate(page_size, page_number, queryset)

    return data


def filter_secretariat_projects(queryset, params, user=None):
    """ Returns data for secretariat projects filtered by project status """

    invoice_status = params.get('status')
    status_filter = project_secretariat_status(invoice_status, user)

    if status_filter is None:
        info = {'message': 'There is no such project status'}
        return Response(info, status=status.HTTP_404_NOT_FOUND)
    else:
        queryset = queryset.filter(
            invoiced__in=status_filter,
            secretariat=True
        )

    page_size = params.get('page_size')
    page_number = params.get('page_number')
    data = paginate(page_size, page_number, queryset)
    return data


def send_message(group, message_type, message):
    """ Send notification to all admin users when project is created """

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            'type': message_type,
            'message': message,
        }
    )


def notification_ws(project_data):
    """ Prepares data for websocket user_project_notification_{user.id}
    creates NotificationProject """

    project = Project.objects.get(id=project_data['id'])
    users = User.objects.filter(role='Admin')
    content = f'Project ({project}) has been added'

    for user in users:
        notification = {
            "user": user.id,
            "project": project.id,
            "content": content
        }
        notification_serializer = NotificationProjectSerializer(data=notification, many=False)

        if notification_serializer.is_valid():
            notification_serializer.save()
            message = {
                'notification': notification_serializer.data,
                'project': project_data
            }
            group = f'user_project_notification_{user.id}'
            message_type = 'project_notification'
            send_message(group, message_type, message)


def project_status_ws(project_status):
    """ When project status is 'In design' or 'Started' change to 'Active' """

    if project_status == 'In design' or project_status == 'Started':
        project_status = 'Active'
    return project_status


def project_data_ws(project_data, project_status, action):
    """ Prepares data for websocket user_project_data_{user.id} """

    users = User.objects.filter(role='Admin')
    if action == 'delete':
        project = project_data.id
    else:
        project = project_data

    for user in users:
        message = {
            'project': project,
            'action': action,
            'project_status': project_status_ws(project_status),
        }
        group = f'user_project_data_{user.id}'
        message_type = 'project_data'
        send_message(group, message_type, message)
