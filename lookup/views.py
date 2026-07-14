from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Lookup
from .serializers import LookupSerializer
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema

@method_decorator(name='list', decorator=swagger_auto_schema(tags=['Lookup Items']))
@method_decorator(name='create', decorator=swagger_auto_schema(tags=['Lookup Items']))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=['Lookup Items']))
@method_decorator(name='update', decorator=swagger_auto_schema(tags=['Lookup Items']))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(tags=['Lookup Items']))
@method_decorator(name='destroy', decorator=swagger_auto_schema(tags=['Lookup Items']))
class LookupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows lookup items (e.g. Roles) to be viewed or edited.
    """
    queryset = Lookup.objects.all()
    serializer_class = LookupSerializer
    permission_classes = [IsAuthenticated]
