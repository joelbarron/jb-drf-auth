import re

from django.apps import apps
from django.contrib.auth import get_user_model
from django.utils.module_loading import import_string

from .conf import get_setting

def get_user_model_cls():
    return get_user_model()

def get_profile_model_cls():
    model_path = get_setting("PROFILE_MODEL")
    if not model_path:
        raise RuntimeError("Missing setting: JB_DRF_AUTH_PROFILE_MODEL = 'app_label.ModelName'")

    try:
        app_label, model_name = model_path.split(".")
    except ValueError as exc:
        raise RuntimeError(
            "Invalid JB_DRF_AUTH_PROFILE_MODEL format. Expected 'app_label.ModelName'"
        ) from exc

    return apps.get_model(app_label, model_name)


def get_device_model_cls():
    model_path = get_setting("DEVICE_MODEL")
    if not model_path:
        raise RuntimeError("Missing setting: JB_DRF_AUTH_DEVICE_MODEL = 'app_label.ModelName'")

    try:
        app_label, model_name = model_path.split(".")
    except ValueError as exc:
        raise RuntimeError(
            "Invalid JB_DRF_AUTH_DEVICE_MODEL format. Expected 'app_label.ModelName'"
        ) from exc

    return apps.get_model(app_label, model_name)


def get_otp_model_cls():
    model_path = get_setting("OTP_MODEL")
    if not model_path:
        raise RuntimeError("Missing setting: JB_DRF_AUTH_OTP_MODEL = 'app_label.ModelName'")

    try:
        app_label, model_name = model_path.split(".")
    except ValueError as exc:
        raise RuntimeError(
            "Invalid JB_DRF_AUTH_OTP_MODEL format. Expected 'app_label.ModelName'"
        ) from exc

    return apps.get_model(app_label, model_name)


def import_from_path(path: str):
    return import_string(path)


def get_sms_provider():
    provider_path = get_setting("SMS_PROVIDER")
    provider_cls = import_string(provider_path)
    return provider_cls()


def get_sms_log_model_cls():
    model_path = get_setting("SMS_LOG_MODEL")
    if not model_path:
        raise RuntimeError("Missing setting: JB_DRF_AUTH_SMS_LOG_MODEL = 'app_label.ModelName'")

    try:
        app_label, model_name = model_path.split(".")
    except ValueError as exc:
        raise RuntimeError(
            "Invalid JB_DRF_AUTH_SMS_LOG_MODEL format. Expected 'app_label.ModelName'"
        ) from exc

    return apps.get_model(app_label, model_name)


def normalize_phone_number(raw_phone: str) -> str:
    if not raw_phone:
        return raw_phone

    phone = raw_phone.strip()
    phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    if phone.startswith("00"):
        phone = f"+{phone[2:]}"

    if phone.startswith("+"):
        digits = re.sub(r"\D", "", phone[1:])
        phone = f"+{digits}"
    else:
        digits = re.sub(r"\D", "", phone)
        default_cc = get_setting("PHONE_DEFAULT_COUNTRY_CODE")
        if default_cc:
            phone = f"+{default_cc}{digits}"
        else:
            raise ValueError("Phone number must include '+' and country code.")

    length = len(phone.replace("+", ""))
    min_len = get_setting("PHONE_MIN_LENGTH")
    max_len = get_setting("PHONE_MAX_LENGTH")
    if length < min_len or length > max_len:
        raise ValueError("Invalid phone number length.")

    return phone


def get_sms_message(code: str, minutes: int) -> str:
    template = get_setting("SMS_OTP_MESSAGE") or "Tu codigo es {code}. Expira en {minutes} minutos."
    message = template.format(code=code, minutes=minutes)
    if not message.isascii():
        return f"Tu codigo es {code}. Expira en {minutes} minutos."
    return message
