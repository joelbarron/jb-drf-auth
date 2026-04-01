from rest_framework import serializers
from django.db import transaction
from django.utils.translation import gettext as _

from jb_drf_auth.conf import get_setting
from jb_drf_auth.services.me import MeService
from jb_drf_auth.utils import get_device_model_cls


class ClientService:
    @staticmethod
    def _normalize_notification_token(notification_token):
        value = str(notification_token or "").strip()
        return value or None

    @staticmethod
    def _claim_notification_token(device_model, device, notification_token):
        normalized_token = ClientService._normalize_notification_token(notification_token)
        if not normalized_token:
            return

        device_pk = getattr(device, "pk", None)
        queryset = device_model.objects.filter(notification_token=normalized_token)
        if device_pk is not None:
            queryset = queryset.exclude(pk=device_pk)
        queryset.update(notification_token=None)

    @staticmethod
    @transaction.atomic
    def upsert_mobile_device(
        *,
        device_model,
        user,
        token,
        platform,
        name,
        notification_token,
    ):
        normalized_token = ClientService._normalize_notification_token(notification_token)
        device, created = device_model.objects.update_or_create(
            user=user,
            token=token,
            defaults={
                "platform": platform,
                "name": name,
                "notification_token": normalized_token,
            },
        )
        ClientService._claim_notification_token(device_model, device, normalized_token)
        return device, created

    @staticmethod
    @transaction.atomic
    def create_mobile_device(
        *,
        device_model,
        user,
        platform,
        name,
        notification_token,
    ):
        normalized_token = ClientService._normalize_notification_token(notification_token)
        device = device_model.objects.create(
            user=user,
            platform=platform,
            name=name,
            token=None,
            notification_token=normalized_token,
        )
        ClientService._claim_notification_token(device_model, device, normalized_token)
        return device

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
            require_notification_token = bool(get_setting("MOBILE_NOTIFICATION_TOKEN_REQUIRED"))
            if require_notification_token and not notification_token:
                raise serializers.ValidationError(
                    {"device": _("notification_token es requerido para cliente movil.")}
                )

            token = device_data.get("token")
            platform = device_data.get("platform", "Unknown Platform")
            name = device_data.get("name", "Unknown Device")
            if token:
                ClientService.upsert_mobile_device(
                    device_model=device_model,
                    user=user,
                    token=token,
                    platform=platform,
                    name=name,
                    notification_token=notification_token,
                )
            else:
                ClientService.create_mobile_device(
                    device_model=device_model,
                    user=user,
                    platform=platform,
                    name=name,
                    notification_token=notification_token,
                )

            response_data = MeService.get_me_mobile(user, profile, tokens)
            response_data["device_registered"] = True
            return response_data

        return MeService.get_me_web(user, profile, tokens)
