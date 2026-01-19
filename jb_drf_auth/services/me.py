from rest_framework import serializers

from jb_drf_auth.conf import get_setting
from jb_drf_auth.serializers.profile import ProfileSerializer
from jb_drf_auth.serializers.user import UserSerializer
from jb_drf_auth.utils import get_device_model_cls, get_profile_model_cls


class MeService:
    @staticmethod
    def get_me_mobile(user, profile, tokens):
        response = UserSerializer(user).data
        if tokens:
            response["tokens"] = tokens
        response["active_profile"] = ProfileSerializer(profile).data
        return response

    @staticmethod
    def get_me_web(user, profile, tokens):
        role = ["admin"]
        status = "active"

        user_payload = {
            "data": {
                "display_name": f"{profile.first_name} {profile.middle_name} {profile.last_name}",
                "photoURL": "",
                "email": user.email,
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
            "terms_and_conditions": getattr(user, "terms_and_conditions", None),
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
            raise serializers.ValidationError({"detail": "Perfil no encontrado."})

        if client == "web":
            return MeService.get_me_web(
                user=user,
                profile=user.get_default_profile(),
                tokens=None,
            )

        if client == "mobile":
            if get_setting("AUTH_SINGLE_SESSION_ON_MOBILE"):
                if device_token:
                    try:
                        device_model = get_device_model_cls()
                    except RuntimeError:
                        raise serializers.ValidationError(
                            {"device": "Configura JB_DRF_AUTH_DEVICE_MODEL para validar dispositivos."}
                        )

                    device = device_model.objects.filter(token=device_token).first()
                    if device is None:
                        raise serializers.ValidationError(
                            {"device": "No se encontro el dispositivo con el token proporcionado."}
                        )
                else:
                    raise serializers.ValidationError(
                        {"device": "Datos del dispositivo requeridos para cliente movil."}
                    )

            return MeService.get_me_mobile(user=user, profile=profile, tokens=None)

        raise serializers.ValidationError({"detail": "Parametro 'client' invalido"})
