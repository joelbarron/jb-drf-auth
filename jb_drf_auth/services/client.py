from rest_framework import serializers
from django.utils.translation import gettext as _

from jb_drf_auth.services.me import MeService
from jb_drf_auth.utils import get_device_model_cls


class ClientService:
    @staticmethod
    def response_for_client(client, user, profile, tokens, device_data):
        if client.lower() == "mobile":
            if not device_data:
                raise serializers.ValidationError(
                    {"device": _("Datos del dispositivo requeridos para cliente movil.")}
                )

            try:
                device_model = get_device_model_cls()
            except RuntimeError:
                raise serializers.ValidationError(
                    {"device": _("Configura JB_DRF_AUTH_DEVICE_MODEL para registrar dispositivos.")}
                )

            notification_token = device_data.get("notification_token")
            if not notification_token:
                raise serializers.ValidationError(
                    {"device": _("notification_token es requerido para cliente movil.")}
                )

            token = device_data.get("token")
            if token:
                device_model.objects.update_or_create(
                    user=user,
                    token=token,
                    defaults={
                        "platform": device_data.get("platform", "Unknown Platform"),
                        "name": device_data.get("name", "Unknown Device"),
                        "notification_token": notification_token,
                    },
                )
            else:
                device_model.objects.create(
                    user=user,
                    platform=device_data.get("platform", "Unknown Platform"),
                    name=device_data.get("name", "Unknown Device"),
                    token=None,
                    notification_token=notification_token,
                )

            response_data = MeService.get_me_mobile(user, profile, tokens)
            response_data["device_registered"] = True
            return response_data

        return MeService.get_me_web(user, profile, tokens)
