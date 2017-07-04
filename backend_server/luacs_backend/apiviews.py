from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import NotFound
from rest_framework import mixins

from . import serializers
from . import models

class CreateListRetrieveViewSet(mixins.CreateModelMixin,
                                mixins.ListModelMixin,
                                mixins.RetrieveModelMixin,
                                viewsets.GenericViewSet):
    """
    A viewset that provides `retrieve`, `create`, and `list` actions.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    """
    pass

#class DeviceViewSet(viewsets.ViewSet):
#    queryset = models.Device.objects.all()
#    
#    def list(self, request):
#        queryset = self.queryset
#        serializer = serializers.DeviceSerializer(
#            queryset, many=True, context={'request': request})
#        return Response(serializer.data)
#    
#    def retrieve(self, request, pk=None):
#        querydata = models.Device.objects.prefetch_related(
#            'required_permission_group__permission_set').get(pk=pk)
#        permissions = querydata.required_permission_group.permission_set.all()
#        serializer = serializers.DeviceSerializer(
#            querydata, permissions=permissions, context={'request': request})
#        return Response(serializer.data)
# TODO restrict all view to terminal specific information
class DeviceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows devices to be viewed.
    """
    queryset = models.Device.objects.all().order_by('pk')
    serializer_class = serializers.DeviceSerializer


class DeviceStatusViewSet(CreateListRetrieveViewSet):
    """
    API endpoint that allows devices status to be viewed and added.
    """
    # TODO allow insertion of new DeviceStatuses for devices associated with the auth token and
    #      newer statuses then the newest
    # TODO restrict asociation with user data to last five entries per device
    queryset = models.DeviceStatus.objects.all()
    serializer_class = serializers.DeviceStatusSerializer


class TerminalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows terminals to be viewed.
    """
    queryset = models.Terminal.objects.all().order_by('pk')
    serializer_class = serializers.TerminalSerializer
    
    @list_route()
    def myself(self, request):
        '''Returns only the terminal object associated with the requests auth token'''
        if request.terminal:
            return Response(self.get_serializer(request.terminal).data)
        else:
            raise NotFound(detail='No terminal is associated with this request.')


class ProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows profiles to be viewed.
    """
    # TODO allow insertion of a new Profile and User
    # TODO allow update of users meta data if they have the magical url
    queryset = models.Profile.objects.all().order_by('pk')
    serializer_class = serializers.ProfileSerializer


class PermissionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Permissions to be viewed or edited.
    """
    # TODO allow insertion of new permissions (and invalidation of any preceeding)
    queryset = (models.Permission.objects.filter(granted_until__gte=timezone.now()) |
                models.Permission.objects.filter(granted_until__isnull=True)).order_by('granted_on')
    serializer_class = serializers.PermissionSerializer


class PermissionGroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Permission Groups to be viewed or edited.
    """
    queryset = models.PermissionGroup.objects.all().order_by('pk')
    serializer_class = serializers.PermissionGroupSerializer
