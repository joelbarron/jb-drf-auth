import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from jb_drf_auth.conf import get_setting
from jb_drf_auth.services.client import ClientService
from jb_drf_auth.services.tokens import TokensService
from jb_drf_auth.utils import get_otp_model_cls, get_profile_model_cls


User = get_user_model()


class OtpService:
    @staticmethod
    def request_otp_code(data):
        otp_length = get_setting("OTP_LENGTH")
        max_value = (10 ** otp_length) - 1
        code = f"{random.randint(0, max_value):0{otp_length}d}"

        otp_model = get_otp_model_cls()
        otp = otp_model.objects.create(
            email=data.get("email"),
            phone=data.get("phone"),
            code=code,
            channel=data["channel"],
            valid_until=timezone.now() + timedelta(minutes=get_setting("OTP_VALID_MINUTES")),
        )

        print("Sending OTP code:", code)

        return {"detail": "Codigo enviado exitosamente.", "channel": otp.channel}

    @staticmethod
    def verify_otp_code(data):
        code = data.get("code")
        email = data.get("email")
        phone = data.get("phone")
        client = data.get("client")
        device_data = data.get("device", None)

        otp_model = get_otp_model_cls()
        otp = otp_model.objects.filter(
            code=code,
            is_used=False,
            valid_until__gte=timezone.now(),
        )
        if email:
            otp = otp.filter(email=email)
        elif phone:
            otp = otp.filter(phone=phone)

        order_field = "-created"
        otp_field_names = {field.name for field in otp_model._meta.get_fields()}
        if "created" not in otp_field_names:
            order_field = "-id"
        otp = otp.order_by(order_field).first()
        if not otp:
            raise serializers.ValidationError({"detail": "Codigo invalido o expirado."})

        otp.is_used = True
        otp.save(update_fields=["is_used"])

        email = otp.email
        phone = otp.phone

        user = None
        if email:
            user = User.objects.filter(email=email).first()
        elif phone:
            user = User.objects.filter(phone=phone).first()

        if not user:
            user = User.objects.create_user(
                email=email,
                phone=phone,
                is_active=True,
            )

            profile_model = get_profile_model_cls()
            profile_model.objects.create(
                user=user,
                role=get_setting("DEFAULT_PROFILE_ROLE"),
                is_default=True,
            )

        if not getattr(user, "is_verified", True):
            user.is_verified = True
            user.save(update_fields=["is_verified"])

        profile = user.get_default_profile()
        tokens = TokensService.get_tokens_for_user(user, profile)
        return ClientService.response_for_client(client, user, profile, tokens, device_data)
