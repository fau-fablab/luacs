from rest_framework import serializers
from django.contrib.auth.models import User

from . import models


class PermissionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Permission
        fields = ('granted_to_id', 'granted_to', 'permission_group', 'valid_until', 'url')


class PermissionGroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.PermissionGroup
        fields = ('name', 'default_permission_days', 'max_unused_days', 'devices', 'url')


class ProfileSerializer(serializers.HyperlinkedModelSerializer):
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    username = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email')
    is_active = serializers.BooleanField(source='user.is_active')

    class Meta:
        model = models.Profile
        permissions = PermissionSerializer(many=True, read_only=True)
        fields = ('id', 'first_name', 'last_name', 'username', 'email', 'is_active', 'id_type',
                  'id_string', 'url')
        #exclude = ()


class DeviceStatusSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.DeviceStatus
        fields = ('start_time', 'device', 'in_operation', 'authorization', 'change_reason')


class DeviceSerializer(serializers.HyperlinkedModelSerializer):
    valid_permissions = PermissionSerializer(
        source='get_valid_permissions', many=True, read_only=True)
    # TODO automatic_logout should serialized as integer seconds not a timedelta string

    class Meta:
        model = models.Device
        fields = ('shortname', 'model_name', 'terminal', 'automatic_logout',
                  'allow_logout_during_operation', 'valid_permissions', 'required_permission_group',
                  'in_operation', 'authorization', 'url')


class TerminalSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Terminal
        fields = ['id', 'devices', 'url']
        #exclude = ['token']

