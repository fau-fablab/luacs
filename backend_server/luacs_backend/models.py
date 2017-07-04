from datetime import timedelta, date, datetime

from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AnonymousUser, User
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver


TZ_MAX = timezone.make_aware(datetime.max)


class Profile(models.Model):
    user = models.OneToOneField(User, related_name='luacs_profile', verbose_name='user',
                                on_delete=models.CASCADE)
    
    # TODO evaluate if id_type should be a choice of options or fall away and be handled on 
    # terminals
    id_type = models.CharField('ID type', max_length=10, null=False, help_text='TODO info here')
    id_string = models.CharField('ID', max_length=255, null=False, help_text='TODO info here')

    def __str__(self):
        return "{} {} ({})".format(self.user.first_name, self.user.last_name, self.user)

    class Meta:
        unique_together = (("id_type", "id_string"),)


class Terminal(models.Model):
    token = models.CharField(
        max_length=20, unique=True, help_text='Used by Terminal to access backend API.')
    # TODO add ip, hostname and use for authentication (optional)
    # TODO add last_seen and currently_online
    # TODO add get_cache_permissions function or transparent caching on terminal?

    def __str__(self):
        ret = "Terminal #{}".format(self.id)
        if self.devices.exists():
            ret += ' ({})'.format(', '.join([d.shortname for d in self.devices.all()]))
        return ret


class Device(models.Model):
    shortname = models.SlugField(primary_key=True, blank=False)
    model_name = models.CharField(max_length=255, null=False, blank=False)
    required_permission_group = models.ForeignKey(
        'PermissionGroup', related_name='devices', null=True, blank=True, on_delete=models.SET_NULL)

    terminal = models.ForeignKey(
        Terminal, related_name='devices',
        null=True, blank=True, on_delete=models.SET_NULL)
    
    # Logout Configuration
    automatic_logout = models.DurationField(
        default=timedelta(0), null=True, blank=True,
        help_text="Duration until user is automatically logged out. If empty/null, no automatic "
                  "logout will occure. If zero or longer, logout will occure depending on 'Allow "
                  " logout during operation', either after last operation ended or since login.")
    allow_logout_during_operation = models.BooleanField(
        default=False,
        help_text="Allows manual logout during operation. Since this would deactivate most devices "
                  "during operation, it is only usefull with devices that can not be "
                  "shutdown/deactivated such as a door that stays open.")
    # TODO deadman switch

    def get_valid_permissions(self):
        return self.required_permission_group.get_valid_permissions()

    @property
    def in_operation(self):
        if self.current_status:
            return self.current_status.in_operation
        else:
            return False

    @property
    def authorization(self):
        if self.current_status:
            return self.current_status.authorization
        else:
            return None

    @property
    def current_status(self):
        try:
            return self.status_history.latest()
        except DeviceStatus.DoesNotExist:
            return None

    def __str__(self):
        return "{} ({})".format(self.shortname, self.model_name)


class DeviceStatus(models.Model):
    device = models.ForeignKey(Device, related_name='status_history', on_delete=models.CASCADE)
    start_time = models.DateTimeField(null=False)
    # TODO Validate that start_time is after most recent start_time for device
    in_operation = models.BooleanField(null=False)
    authorization = models.ForeignKey("Permission", null=True, blank=True, related_name='usage',
                                      on_delete=models.SET_NULL)
    # TODO Validate that authorization was valid at start_time and for device
    change_reason = models.TextField(blank=True)

    @property
    def end_time(self):
        try:
            return DeviceStatus.objects.filter(
                device=self.device, start_time__gte=self.start_time, id__gt=self.id
                ).order_by('start_time')[:1].get().start_time
        except DeviceStatus.DoesNotExist:
            return None

    def __str__(self):
        op = "IN" if self.in_operation else "NOT IN"
        if self.end_time is None:
            r = "From {}, {} has been {} operation".format(
                self.start_time, self.device, op)
        else:
            r = "{} - {}, {} was {} operation".format(
                self.start_time, self.end_time, self.device, op)
        if self.authorization:
            return r + ", authorized by {}".format(self.authorization.granted_to)
        else:
            return r + ", NOT authorized"
            

    class Meta:
        ordering = ['-start_time', 'id']
        get_latest_by = 'start_time'


class PermissionGroup(models.Model):
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(
        Profile,
        through='Permission',
        through_fields=('permission_group', 'granted_to'))
    default_permission_days = models.PositiveSmallIntegerField(
        'default permission duration (in days)', default=365, null=True, blank=True,
        help_text='Default expiration time. If null/not set, permission will not expire.')
    max_unused_days = models.PositiveSmallIntegerField(
        default=90, null=True, blank=True,
        help_text='Max. days since last use for permission to still be valid. If null/not set, '
                  'usage is not necessary.')

    def get_valid_permissions(self):
        # TODO make this work in the DB and using PermissionManager
        return [p for p in (self.permission_set.filter(granted_until__gte=timezone.now()) |
                            self.permission_set.filter(granted_until__isnull=True))
                if p.valid_now]

    def __str__(self):
        return "{} permission".format(self.name)


class Permission(models.Model):
    granted_to = models.ForeignKey(
        Profile, related_name='permissions', on_delete=models.CASCADE)
    granted_on = models.DateTimeField(auto_now_add=True)
    permission_group = models.ForeignKey(
        PermissionGroup, on_delete=models.CASCADE)
    granted_until = models.DateTimeField(
        null=True, blank=True, help_text='If not set, unlimited permission is granted.')
    granted_by = models.ForeignKey(Profile, null=True, blank=True, related_name='+',
                                   on_delete=models.SET_NULL)

    @property
    def last_used(self):
        try:
            return self.usage.order_by('-start_time')[:1].get()
        except DeviceStatus.DoesNotExist:
            return self.granted_on

    # TODO move this into the DB and make preselection in PermissionManager(models.Manager)
    @property
    def valid_until(self):
        if self.granted_until == None:
            return TZ_MAX
        else:
            return min(self.last_used + timedelta(days=self.permission_group.max_unused_days),
                       self.granted_until)

    # TODO move this into the DB and make preselection in PermissionManager(models.Manager)
    @property
    def valid_now(self):
        # FIXME Use admin flag or special group for blanket permission?
        return self.valid_until >= timezone.now()

    def withdraw(self):
        if not self.valid_now:
            # Already invalid, nothing to do
            return
        else:
            # Set permission to expire now
            self.granted_until = timezone.now()

    # TODO make sure no overlapping permissions exist
    # https://docs.djangoproject.com/en/1.11/ref/models/instances/#validating-objects

    def __str__(self):
        until = self.valid_until if self.valid_until != TZ_MAX else "forever"
        return "{} has {} until {}".format(
            self.granted_to, self.permission_group, until)
