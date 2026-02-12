"""Profile serializers."""

from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from jb_drf_auth.image_utils import optimize_profile_picture
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


class ProfilePictureUpdateSerializer(serializers.Serializer):
    profile = serializers.IntegerField(required=False)
    picture = Base64ImageField(required=True, allow_null=False)

    def _resolve_profile(self):
        request = self.context["request"]
        user = request.user
        profile_model = get_profile_model_cls()
        profile_id = self.validated_data.get("profile")
        queryset = profile_model.objects.filter(user=user)

        if profile_id is not None:
            profile = queryset.filter(id=profile_id).first()
        else:
            profile = user.get_default_profile()
            if profile is None:
                profile = queryset.first()

        if profile is None:
            raise serializers.ValidationError({"profile": _("Perfil no encontrado.")})
        if not hasattr(profile, "picture"):
            raise serializers.ValidationError(
                {"picture": _("El modelo de perfil no tiene el campo picture.")}
            )
        return profile

    def save(self, **kwargs):
        profile = self._resolve_profile()
        optimized_picture = optimize_profile_picture(self.validated_data["picture"])
        profile.picture = optimized_picture
        profile.save()
        return profile
