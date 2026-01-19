from rest_framework import serializers

from jb_drf_auth.conf import get_setting
from jb_drf_auth.serializers.device import DevicePayloadSerializer
from jb_drf_auth.services.login import LoginService


CLIENT_CHOICES = get_setting("CLIENT_CHOICES")


class BasicLoginSerializer(serializers.Serializer):
    login = serializers.CharField()
    password = serializers.CharField(write_only=True)
    client = serializers.ChoiceField(choices=CLIENT_CHOICES)
    device = DevicePayloadSerializer(write_only=True, required=False)

    def validate(self, data):
        login = data.get("login")
        password = data.get("password")
        client = data.get("client")
        device_data = data.get("device")
        return LoginService.basic_login(login, password, client, device_data)


class SwitchProfileSerializer(serializers.Serializer):
    profile = serializers.IntegerField()
    client = serializers.ChoiceField(choices=CLIENT_CHOICES)
    device = DevicePayloadSerializer(write_only=True, required=False)
