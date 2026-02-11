"""Profile serializers."""

from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from jb_drf_auth.utils import get_profile_model_cls


def _safe_exclude_fields(model, fields):
    model_fields = {field.name for field in model._meta.get_fields()}
    return tuple(field for field in fields if field in model_fields)


class ProfileSerializer(serializers.ModelSerializer):
    picture = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = get_profile_model_cls()
        exclude = _safe_exclude_fields(
            model,
            ("deleted", "deleted_by_cascade", "user"),
        )

    def create(self, validated_data):
        user = self.context["request"].user
        if not user.is_authenticated:
            raise serializers.ValidationError(_("Debes estar autenticado para crear un perfil."))
        validated_data["user"] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if user.is_authenticated and user == instance.user:
            return super().update(instance, validated_data)
        raise serializers.ValidationError(_("Solo puedes actualizar tu propio perfil."))

    def delete(self, instance):
        user = self.context["request"].user
        if user.is_authenticated and user == instance.user:
            return super().delete(instance)
        raise serializers.ValidationError(_("Solo puedes eliminar tus propios perfiles."))
