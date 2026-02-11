from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, NotFound
from django.utils.translation import gettext as _

from jb_drf_auth.backends import EmailOrUsernameModelBackend
from jb_drf_auth.conf import get_setting
from jb_drf_auth.services.client import ClientService
from jb_drf_auth.services.tokens import TokensService


CLIENT_CHOICES = get_setting("CLIENT_CHOICES")


class LoginService:
    @staticmethod
    def basic_login(login, password, client, device_data):
        auth_backend = EmailOrUsernameModelBackend()
        normalized_client = client.lower()

        if normalized_client not in CLIENT_CHOICES:
            raise serializers.ValidationError(_("Cliente no valido. Debe ser 'web' o 'mobile'."))

        # Web login does not require or use device payload.
        if normalized_client == "web":
            device_data = None

        user = auth_backend.authenticate(username=login, password=password)

        if user is None:
            raise AuthenticationFailed(_("Credenciales invalidas."))
        if not getattr(user, "is_verified", True):
            raise AuthenticationFailed(_("Esta cuenta no esta verificada."))
        if not getattr(user, "is_active", True):
            raise AuthenticationFailed(_("Esta cuenta esta inactiva."))
        if getattr(user, "deleted", None):
            raise AuthenticationFailed(_("Esta cuenta esta eliminada."))

        profile = user.get_default_profile()
        tokens = TokensService.get_tokens_for_user(user=user, profile=profile)
        return ClientService.response_for_client(
            normalized_client, user, profile, tokens, device_data
        )

    @staticmethod
    def switch_profile(user, profile_id, client, device_data):
        profiles_qs = user.profiles.filter(is_active=True)
        profile_field_names = {field.name for field in user.profiles.model._meta.get_fields()}
        if "deleted" in profile_field_names:
            profiles_qs = profiles_qs.filter(deleted=None)
        try:
            profile = profiles_qs.get(id=profile_id)
        except user.profiles.model.DoesNotExist:
            raise NotFound(_("Perfil no encontrado o no pertenece al usuario."))

        tokens = TokensService.get_tokens_for_user(user, profile)
        return ClientService.response_for_client(client, user, profile, tokens, device_data)
