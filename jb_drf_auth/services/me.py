from rest_framework import serializers
from rest_framework.exceptions import NotFound
from django.utils.translation import gettext as _

from jb_drf_auth.conf import get_setting
from jb_drf_auth.serializers.profile import ProfileSerializer
from jb_drf_auth.serializers.user import UserSerializer
from jb_drf_auth.utils import get_device_model_cls, get_profile_model_cls


class MeService:
    @staticmethod
    def _settings_payload(value):
        return value if isinstance(value, dict) else {}

    @staticmethod
    def profile_completion_required(profile):
        first_name = (getattr(profile, "first_name", "") or "").strip()
        last_name_1 = (getattr(profile, "last_name_1", "") or "").strip()
        last_name_2 = (getattr(profile, "last_name_2", "") or "").strip()
        has_first_name = bool(first_name)
        has_last_name = bool(last_name_1 or last_name_2)
        return not (has_first_name and has_last_name)

    @staticmethod
    def _profile_photo_url(profile):
        picture = getattr(profile, "picture", None)
        if not picture:
            return None
        try:
            return picture.url
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _web_role_map_from_settings():
        role_choices = get_setting("PROFILE_ROLE_CHOICES") or ()
        role_map = {}

        for choice in role_choices:
            if not isinstance(choice, (tuple, list)) or not choice:
                continue
            raw_role = str(choice[0] or "").strip().upper()
            if not raw_role:
                continue
            role_map[raw_role] = raw_role.lower()

        return role_map

    @staticmethod
    def _web_role_from_profile(profile):
        raw_role = str(getattr(profile, "role", "") or "").strip().upper()
        role_map = MeService._web_role_map_from_settings()
        if raw_role in role_map:
            return [role_map[raw_role]]
        if raw_role:
            return [raw_role.lower()]
        return ["patient"]

    @staticmethod
    def get_me_mobile(user, profile, tokens):
        response = UserSerializer(user).data
        if tokens:
            response["tokens"] = tokens
        response["active_profile"] = ProfileSerializer(profile).data
        response["user_settings"] = MeService._settings_payload(getattr(user, "settings", None))
        response["profile_settings"] = MeService._settings_payload(getattr(profile, "settings", None))
        response["profile_completion_required"] = MeService.profile_completion_required(profile)
        return response

    @staticmethod
    def get_me_web(user, profile, tokens):
        role = MeService._web_role_from_profile(profile)
        status = "active"

        user_payload = {
            "data": {
                "display_name": profile.display_name,
                "full_name": profile.full_name,
                "photoURL": MeService._profile_photo_url(profile),
                "email": user.email,
                "phone": getattr(user, "phone", None),
                "username": user.username,
                "birthday": profile.birthday,
                "shortcuts": [],
            },
            "login_redirect_url": "/home",
            "role": role,
            "status": status,
        }

        response = {
            "user": user_payload,
            "active_profile": ProfileSerializer(profile).data,
            "user_settings": MeService._settings_payload(getattr(user, "settings", None)),
            "profile_settings": MeService._settings_payload(getattr(profile, "settings", None)),
            "terms_and_conditions": getattr(user, "terms_and_conditions", None),
            "profile_completion_required": MeService.profile_completion_required(profile),
        }

        if tokens:
            response["tokens"] = tokens

        return response

    @staticmethod
    def get_me(user, client, profile_id, device_token=None):
        profile_model = get_profile_model_cls()
        try:
            profile = profile_model.objects.get(id=profile_id)
        except profile_model.DoesNotExist:
            raise NotFound(_("Perfil no encontrado."))

        if client == "web":
            return MeService.get_me_web(
                user=user,
                profile=profile,
                tokens=None,
            )

        if client == "mobile":
            if get_setting("AUTH_SINGLE_SESSION_ON_MOBILE"):
                if device_token:
                    try:
                        device_model = get_device_model_cls()
                    except RuntimeError:
                        raise serializers.ValidationError(
                            {"device": _("Configura JB_DRF_AUTH_DEVICE_MODEL para validar dispositivos.")}
                        )

                    device = device_model.objects.filter(token=device_token).first()
                    if device is None:
                        raise NotFound(_("No se encontro el dispositivo con el token proporcionado."))
                else:
                    raise serializers.ValidationError(
                        {"device": _("Datos del dispositivo requeridos para cliente movil.")}
                    )

            return MeService.get_me_mobile(user=user, profile=profile, tokens=None)

        raise serializers.ValidationError({"detail": _("Parametro 'client' invalido")})
