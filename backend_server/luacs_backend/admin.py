from django.contrib import admin
from django.contrib.auth.models import User

from .models import Profile, Device, DeviceStatus, Permission, PermissionGroup, Terminal


# TODO add permission model for django users?
# AdminViews
@admin.register(PermissionGroup)
class PermissionGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'devices', 'member_count', 'default_permission_days', 'max_unused_days')
    fields = ('name', 'default_permission_days', 'max_unused_days')

    def devices(self, obj):
        return ", ".join([d.shortname for d in obj.devices.all()])

    def member_count(self, obj):
        return len(obj.members.all())


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('granted_to', 'permission_group', 'granted_until', 'last_used', 'valid_now')
    readonly_fields = ('last_used', 'granted_on')
    fieldsets = ((None, {'fields': ('granted_to', 'permission_group', 'granted_until', 
                                    'last_used')}),
                 ('Granter info', {'fields': ('granted_by', 'granted_on'),
                                   'classes': ['collapse']}))

    def has_delete_permission(self, request, obj=None):
        return False


class PermissionProfileInline(admin.StackedInline):
    model = Permission
    fk_name = 'granted_to'
    extra = 1

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    def last_name(self, obj):
        return obj.user.last_name

    def first_name(self, obj):
        return obj.user.first_name

    def email(self, obj):
        return obj.user.email

    fields = ('user', ('id_type', 'id_string'),)
    list_display = ('last_name', 'first_name', 'email', 'id_type', 'id_string')
    inlines = [PermissionProfileInline]


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('shortname', 'model_name', 'required_permission_group', 'terminal')


@admin.register(Terminal)
class TerminalAdmin(admin.ModelAdmin):
    list_display = ('id', 'token', 'devices_list')
    fields = ('token', )

    def devices_list(self, obj):
        return ", ".join([d.shortname for d in obj.devices.all()])


@admin.register(DeviceStatus)
class DeviceStatusAdmin(admin.ModelAdmin):
    # Original: https://gist.github.com/aaugustin/1388243
    actions = None

    # We cannot call super().get_fields(request, obj) because that method calls
    # get_readonly_fields(request, obj), causing infinite recursion. Ditto for
    # super().get_form(request, obj). So we  assume the default ModelForm.
    # Disable all write access
    #def has_add_permission(self, request, obj=None):
    #    return False

    #def has_change_permission(self, request, obj=None):
    #    return (request.method in ['GET', 'HEAD'] and
    #            super().has_change_permission(request, obj))

    def has_delete_permission(self, request, obj=None):
        return False

    #def get_readonly_fields(self, request, obj=None):
    #    return self.fields or [f.name for f in self.model._meta.fields]
