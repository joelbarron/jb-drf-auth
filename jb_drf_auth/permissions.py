import secrets

from django.contrib.auth import get_user_model
from rest_framework import permissions

from jb_drf_auth.conf import get_setting


class BootstrapTokenOrAdmin(permissions.BasePermission):
    message = "Bootstrap token required."

    def has_permission(self, request, view):
        user = request.user
        if user and user.is_authenticated and user.is_superuser:
            return True

        user_model = get_user_model()
        if user_model.objects.filter(is_superuser=True).exists():
            return False

        token = request.headers.get("X-Admin-Bootstrap-Token")
        bootstrap_token = get_setting("ADMIN_BOOTSTRAP_TOKEN") or ""
        if not bootstrap_token or not token:
            return False

        return secrets.compare_digest(token, bootstrap_token)
