from __future__ import unicode_literals

from rest_framework.permissions import BasePermission
from rest_framework.authentication import get_authorization_header
from rest_framework import exceptions

from . import models


# Helper grant permission to Terminals according to their token passed via http headers:
# -H "Authorization: Token Bearer 12345678901234567890" (curl)
# Using CoreAPI:
# >>> auth = coreapi.auth.TokenAuthentication(scheme='Token', token='123123123')
# $ coreapi credentials add localhost:8000 "Token 123123123"
class TerminalTokenOrAdminUserPermission(BasePermission):
    keyword = 'Token'
    
    def has_permission(self, request, view):
        request.terminal = None
        if request.user and request.user.is_superuser:
            return True

        auth = get_authorization_header(request).split()
        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None
        
        if len(auth) == 1:
            msg = _('Invalid token header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _('Invalid token header. Token string should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)

        try:
            token = auth[1].decode()
        except UnicodeError:
            msg = _('Invalid token header. Token string should not contain invalid characters.')
            raise exceptions.AuthenticationFailed(msg)
        
        try:
            request.terminal = models.Terminal.objects.get(token=token)
            return True
        except models.Terminal.DoesNotExist:
            return False

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)
