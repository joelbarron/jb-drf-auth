"""User serializer."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from jb_drf_auth.serializers.profile import ProfileSerializer


def _safe_exclude_fields(model, fields):
    model_fields = {field.name for field in model._meta.get_fields()}
    return tuple(field for field in fields if field in model_fields)


class UserSerializer(serializers.ModelSerializer):
    profiles = ProfileSerializer(read_only=True, many=True)
    language = serializers.SerializerMethodField()
    timezone = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        exclude = _safe_exclude_fields(
            model,
            (
                "deleted",
                "deleted_by_cascade",
                "password",
                "is_superuser",
                "is_active",
                "is_staff",
                "last_login",
                "created",
                "modified",
            ),
        )

    def get_language(self, obj):
        return obj.language

    def get_timezone(self, obj):
        return obj.timezone
