"""Serializers for device payloads and models."""

from rest_framework import serializers

from jb_drf_auth.utils import get_device_model_cls


class DevicePayloadSerializer(serializers.Serializer):
    platform = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    token = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    notification_token = serializers.CharField(required=False, allow_blank=True, allow_null=True)


def _safe_exclude_fields(model, fields):
    model_fields = {field.name for field in model._meta.get_fields()}
    return tuple(field for field in fields if field in model_fields)


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        exclude = ()

    def get_fields(self):
        if self.Meta.model is None:
            self.Meta.model = get_device_model_cls()
            self.Meta.exclude = _safe_exclude_fields(
                self.Meta.model, ("deleted", "deleted_by_cascade", "user")
            )
        return super().get_fields()
