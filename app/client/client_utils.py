from core.models import Client
from django.db.models import Q
from rest_framework.response import Response

from .serializers import ClientSerializer


def search_client(params):
    search = params.get('q')

    queryset = Client.objects.filter(
        (Q(name__icontains=search) |
         Q(email__icontains=search) |
         Q(phone_number__icontains=search) |
         Q(address__icontains=search))
    )

    serializer = ClientSerializer(queryset, many=True)
    return Response(serializer.data)
