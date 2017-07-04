from django.conf.urls import url, include
from rest_framework import routers

from . import views
from . import apiviews

router = routers.DefaultRouter()
router.register(r'devices', apiviews.DeviceViewSet)
router.register(r'devices_status', apiviews.DeviceStatusViewSet)
router.register(r'terminals', apiviews.TerminalViewSet)
router.register(r'profiles', apiviews.ProfileViewSet)
router.register(r'permissions', apiviews.PermissionViewSet)
router.register(r'permission_groups', apiviews.PermissionGroupViewSet)

urlpatterns = [
    url(r'^api/', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
