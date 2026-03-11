from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class UsernameAvailabilitySerializer(serializers.Serializer):
    username = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)


class EmailAvailabilitySerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class PhoneAvailabilitySerializer(serializers.Serializer):
    phone = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)


class AvailabilityResponseSerializer(serializers.Serializer):
    available = serializers.BooleanField()
    field = serializers.CharField()
    value = serializers.CharField(allow_blank=True)
    detail = serializers.CharField(required=False)


def unavailable_detail(field_name: str) -> str:
    if field_name == "email":
        return str(_("Ya existe un usuario con este correo."))
    if field_name == "username":
        return str(_("El nombre de usuario ya esta en uso."))
    return str(_("Valor no disponible."))
