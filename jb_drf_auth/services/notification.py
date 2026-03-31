"""Reusable notification service (inbox + Expo push)."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Iterable

import requests
from django.conf import settings
from django.db import transaction

from jb_drf_auth.utils import get_device_model_cls, get_notification_model_cls

logger = logging.getLogger(__name__)

EXPO_PUSH_SEND_URL = "https://exp.host/--/api/v2/push/send"
EXPO_PUSH_RECEIPTS_URL = "https://exp.host/--/api/v2/push/getReceipts"
EXPO_SEND_CHUNK = 100
EXPO_RECEIPT_CHUNK = 300


@dataclass
class ExpoMessage:
    token: str
    payload: dict


class NotificationService:
    """Creates inbox records and dispatches push notifications."""

    @staticmethod
    def _notification_model():
        return get_notification_model_cls()

    @staticmethod
    def _device_model():
        return get_device_model_cls()

    @staticmethod
    def _has_field(model_cls, field_name: str) -> bool:
        return any(getattr(field, "name", "") == field_name for field in model_cls._meta.fields)

    @staticmethod
    def _is_push_enabled() -> bool:
        return bool(getattr(settings, "EXPO_PUSH_ENABLED", True))

    @staticmethod
    def _expo_headers() -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        access_token = str(getattr(settings, "EXPO_PUSH_ACCESS_TOKEN", "") or "").strip()
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return headers

    @staticmethod
    def _iter_chunks(items: list, size: int):
        for index in range(0, len(items), size):
            yield items[index : index + size]

    @staticmethod
    def _post_with_retry(url: str, payload: dict | list, *, max_attempts: int = 3) -> requests.Response:
        attempt = 0
        while True:
            attempt += 1
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=NotificationService._expo_headers(),
                    timeout=10,
                )
                if response.status_code >= 500:
                    raise RuntimeError(f"Expo push temporary error ({response.status_code}).")
                return response
            except Exception as exc:
                if attempt >= max_attempts:
                    raise
                sleep_seconds = 0.4 * attempt
                logger.warning(
                    "expo_push_retry url=%s attempt=%s error=%s",
                    url,
                    attempt,
                    exc,
                )
                time.sleep(sleep_seconds)

    @staticmethod
    def _notification_tokens_for_profile(profile) -> list[str]:
        device_model = NotificationService._device_model()
        queryset = device_model.objects.filter(user_id=getattr(profile, "user_id", None))
        if NotificationService._has_field(device_model, "deleted"):
            queryset = queryset.filter(deleted__isnull=True)
        queryset = queryset.exclude(notification_token__isnull=True).exclude(notification_token="")
        tokens = queryset.values_list("notification_token", flat=True).distinct()
        return [str(token).strip() for token in tokens if str(token).strip()]

    @staticmethod
    def _clear_invalid_push_tokens(tokens: Iterable[str]):
        token_values = [str(item).strip() for item in tokens if str(item).strip()]
        if not token_values:
            return
        device_model = NotificationService._device_model()
        device_model.objects.filter(notification_token__in=token_values).update(notification_token=None)

    @staticmethod
    def _build_push_messages(notification) -> list[ExpoMessage]:
        tokens = NotificationService._notification_tokens_for_profile(notification.profile)
        if not tokens:
            return []

        base_data = {}
        if isinstance(getattr(notification, "data", None), dict):
            base_data.update(notification.data)
        base_data["notificationId"] = notification.id
        action_path = getattr(notification, "action_path", None)
        if action_path:
            base_data["actionPath"] = action_path

        messages: list[ExpoMessage] = []
        for token in tokens:
            payload = {
                "to": token,
                "title": notification.title,
                "body": notification.body or "",
                "data": base_data,
                "sound": "default",
            }
            messages.append(ExpoMessage(token=token, payload=payload))
        return messages

    @staticmethod
    def _dispatch_push(notification):
        if not NotificationService._is_push_enabled():
            return

        messages = NotificationService._build_push_messages(notification)
        if not messages:
            return

        invalid_tokens: set[str] = set()
        receipt_ticket_to_token: dict[str, str] = {}

        for message_chunk in NotificationService._iter_chunks(messages, EXPO_SEND_CHUNK):
            payload = [item.payload for item in message_chunk]
            token_by_index = {index: item.token for index, item in enumerate(message_chunk)}
            try:
                response = NotificationService._post_with_retry(
                    EXPO_PUSH_SEND_URL,
                    payload=payload,
                )
                body = response.json() if response.content else {}
            except Exception as exc:
                logger.exception(
                    "expo_push_send_failed notification_id=%s error=%s",
                    getattr(notification, "id", None),
                    exc,
                )
                continue

            data = body.get("data")
            if not isinstance(data, list):
                continue

            for index, item in enumerate(data):
                token = token_by_index.get(index)
                if not isinstance(item, dict):
                    continue
                if item.get("status") == "ok" and item.get("id"):
                    receipt_ticket_to_token[str(item.get("id"))] = token or ""
                    continue

                details = item.get("details") if isinstance(item.get("details"), dict) else {}
                error_code = str(details.get("error") or item.get("message") or "").strip()
                if error_code == "DeviceNotRegistered" and token:
                    invalid_tokens.add(token)

        receipt_ids = [receipt_id for receipt_id in receipt_ticket_to_token if receipt_id]
        for receipt_chunk in NotificationService._iter_chunks(receipt_ids, EXPO_RECEIPT_CHUNK):
            try:
                response = NotificationService._post_with_retry(
                    EXPO_PUSH_RECEIPTS_URL,
                    payload={"ids": receipt_chunk},
                )
                body = response.json() if response.content else {}
            except Exception as exc:
                logger.exception(
                    "expo_push_receipts_failed notification_id=%s error=%s",
                    getattr(notification, "id", None),
                    exc,
                )
                continue

            receipt_data = body.get("data")
            if not isinstance(receipt_data, dict):
                continue

            for receipt_id, result in receipt_data.items():
                if not isinstance(result, dict):
                    continue
                status = str(result.get("status") or "").lower()
                if status == "ok":
                    continue
                details = result.get("details") if isinstance(result.get("details"), dict) else {}
                error_code = str(details.get("error") or "").strip()
                if error_code == "DeviceNotRegistered":
                    token = receipt_ticket_to_token.get(str(receipt_id))
                    if token:
                        invalid_tokens.add(token)

        if invalid_tokens:
            NotificationService._clear_invalid_push_tokens(invalid_tokens)

    @staticmethod
    def _channel_value(name: str) -> str:
        notification_model = NotificationService._notification_model()
        channel_enum = getattr(notification_model, "Channel", None)
        if channel_enum and hasattr(channel_enum, name):
            return getattr(channel_enum, name)
        return name

    @staticmethod
    @transaction.atomic
    def emit(
        *,
        profile,
        notification_type: str,
        title: str,
        body: str = "",
        data: dict | None = None,
        action_path: str | None = None,
        channel: str | None = None,
        dedupe_key: str | None = None,
    ):
        profile_id = getattr(profile, "id", None)
        if not profile_id:
            raise ValueError("profile is required.")

        notification_model = NotificationService._notification_model()
        normalized_channel = str(channel or "").strip() or NotificationService._channel_value("BOTH")
        normalized_dedupe = str(dedupe_key or "").strip() or None

        queryset = notification_model.objects.filter(profile_id=profile_id)
        if NotificationService._has_field(notification_model, "deleted"):
            queryset = queryset.filter(deleted__isnull=True)

        if normalized_dedupe:
            existing = queryset.filter(dedupe_key=normalized_dedupe).first()
            if existing:
                return existing

        notification = notification_model.objects.create(
            profile=profile,
            type=notification_type,
            title=(title or "").strip()[:255],
            body=(body or "").strip(),
            data=data or {},
            action_path=(action_path or "").strip() or None,
            channel=normalized_channel,
            dedupe_key=normalized_dedupe,
        )

        if normalized_channel in {
            NotificationService._channel_value("BOTH"),
            NotificationService._channel_value("PUSH"),
        }:
            NotificationService._dispatch_push(notification)

        return notification
