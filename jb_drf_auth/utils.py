import re
from copy import deepcopy
from typing import Any

from django.conf import settings
from django.apps import apps
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils.module_loading import import_string

from .conf import ROOT_SETTING, get_setting, get_social_settings
from .email_templates import DEFAULT_EMAIL_TEMPLATES, DEFAULT_MAILING

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


def get_email_provider():
    provider_path = get_setting("EMAIL_PROVIDER")
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


def get_email_log_model_cls():
    model_path = get_setting("EMAIL_LOG_MODEL")
    if not model_path:
        raise RuntimeError("Missing setting: JB_DRF_AUTH_EMAIL_LOG_MODEL = 'app_label.ModelName'")

    try:
        app_label, model_name = model_path.split(".")
    except ValueError as exc:
        raise RuntimeError(
            "Invalid JB_DRF_AUTH_EMAIL_LOG_MODEL format. Expected 'app_label.ModelName'"
        ) from exc

    return apps.get_model(app_label, model_name)


def get_social_account_model_cls():
    model_path = get_setting("SOCIAL_ACCOUNT_MODEL")
    if not model_path:
        raise RuntimeError("Missing setting: JB_DRF_AUTH_SOCIAL_ACCOUNT_MODEL = 'app_label.ModelName'")

    try:
        app_label, model_name = model_path.split(".")
    except ValueError as exc:
        raise RuntimeError(
            "Invalid JB_DRF_AUTH_SOCIAL_ACCOUNT_MODEL format. Expected 'app_label.ModelName'"
        ) from exc

    return apps.get_model(app_label, model_name)


def get_social_provider(provider: str):
    social_settings = get_social_settings()
    providers = social_settings.get("PROVIDERS", {})
    if not isinstance(providers, dict) or provider not in providers:
        raise RuntimeError(f"Unsupported social provider: {provider}")

    provider_cfg = providers.get(provider, {})
    if not isinstance(provider_cfg, dict):
        raise RuntimeError(f"Invalid social provider configuration for: {provider}")

    provider_path = provider_cfg.get("CLASS")
    if not provider_path:
        raise RuntimeError(f"Missing social provider class for: {provider}")

    provider_cls = import_string(provider_path)
    return provider_cls(provider=provider, provider_settings=provider_cfg)


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


def _deep_merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge_dict(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def get_mailing_settings() -> dict[str, Any]:
    merged = deepcopy(DEFAULT_MAILING)

    root = getattr(settings, ROOT_SETTING, None)
    if isinstance(root, dict):
        root_mailing = root.get("MAILING")
        if isinstance(root_mailing, dict):
            merged = _deep_merge_dict(merged, root_mailing)

    project_mailing = getattr(settings, "MAILING", None)
    if isinstance(project_mailing, dict):
        merged = _deep_merge_dict(merged, project_mailing)

    return merged


def get_email_template(name: str):
    mailing = get_mailing_settings()
    mailing_templates = mailing.get("templates")
    if isinstance(mailing_templates, dict) and name in mailing_templates:
        return mailing_templates[name]

    templates = get_setting("EMAIL_TEMPLATES")
    if isinstance(templates, dict) and name in templates:
        return templates[name]

    return DEFAULT_EMAIL_TEMPLATES.get(name, {})


def _render_template_value(value: Any, context: dict[str, Any]):
    if callable(value):
        return value(context)
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    try:
        return value.format(**context)
    except Exception:
        return value


def render_email_template(name: str, context: dict):
    mailing = get_mailing_settings()
    template = get_email_template(name)
    render_context = dict(context or {})
    render_context.setdefault("mailing", mailing)

    subject = _render_template_value(template.get("subject", ""), render_context) or ""

    text_template = template.get("text_template")
    if text_template:
        text_body = render_to_string(str(text_template), render_context)
    else:
        text_body = _render_template_value(template.get("text", ""), render_context) or ""

    html_template = template.get("html_template")
    if html_template:
        html_body = render_to_string(str(html_template), render_context)
    else:
        html_body = _render_template_value(template.get("html"), render_context)

    text_body = str(text_body or "").strip()
    if not text_body:
        text_body = str(subject or "").strip()

    return subject, text_body, html_body
