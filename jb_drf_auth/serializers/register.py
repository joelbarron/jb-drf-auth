"""Register serializer."""

from rest_framework import serializers

from jb_drf_auth.services.register import RegisterService


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(min_length=8, max_length=128)
    password_confirm = serializers.CharField(min_length=8, max_length=128)
    first_name = serializers.CharField(max_length=100)
    middle_name = serializers.CharField(max_length=150, allow_blank=True, allow_null=True)
    last_name = serializers.CharField(max_length=150)
    birthday = serializers.DateField(required=True)
    gender = serializers.CharField(max_length=50)
    role = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def create(self, validated_data):
        return RegisterService.register_user(
            email=validated_data["email"],
            username=validated_data.get("username"),
            password=validated_data["password"],
            password_confirm=validated_data["password_confirm"],
            first_name=validated_data["first_name"],
            middle_name=validated_data.get("middle_name"),
            last_name=validated_data["last_name"],
            birthday=validated_data["birthday"],
            gender=validated_data["gender"],
            role=validated_data.get("role"),
        )
