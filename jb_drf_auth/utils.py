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
