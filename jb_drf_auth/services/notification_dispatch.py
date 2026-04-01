"""High-level notification dispatch helpers (single and broadcast)."""

from __future__ import annotations

import time

from jb_drf_auth.services.notification import NotificationService
from jb_drf_auth.utils import get_profile_model_cls


class NotificationDispatchService:
    """Dispatch notifications to one profile or many profiles."""

    @staticmethod
    def _profile_queryset():
        profile_model = get_profile_model_cls()
        queryset = profile_model.objects.all()
        if any(getattr(field, "name", "") == "deleted" for field in profile_model._meta.fields):
            queryset = queryset.filter(deleted__isnull=True)
        if any(getattr(field, "name", "") == "is_active" for field in profile_model._meta.fields):
            queryset = queryset.filter(is_active=True)
        return queryset

    @staticmethod
    def send_to_profile(
        *,
        profile_id: int,
        notification_type: str,
        title: str,
        body: str = "",
        data: dict | None = None,
        action_path: str | None = None,
        channel: str | None = None,
        dedupe_key: str | None = None,
    ):
        profile = NotificationDispatchService._profile_queryset().filter(id=profile_id).first()
        if not profile:
            raise ValueError("Profile not found.")
        notification = NotificationService.emit(
            profile=profile,
            notification_type=notification_type,
            title=title,
            body=body,
            data=data,
            action_path=action_path,
            channel=channel,
            dedupe_key=dedupe_key,
        )
        return notification

    @staticmethod
    def broadcast(
        *,
        notification_type: str,
        title: str,
        body: str = "",
        data: dict | None = None,
        action_path: str | None = None,
        channel: str | None = None,
        dedupe_key_prefix: str | None = None,
        profile_ids: list[int] | None = None,
    ) -> dict:
        queryset = NotificationDispatchService._profile_queryset()
        if profile_ids:
            queryset = queryset.filter(id__in=profile_ids)

        sent = 0
        skipped = 0
        sent_push = 0
        sent_in_app_only = 0
        notifications = []
        timestamp_seed = int(time.time() * 1000)
        dedupe_prefix = (dedupe_key_prefix or "").strip() or f"broadcast:{timestamp_seed}"
        normalized_channel = str(channel or "").strip() or NotificationService._channel_value("BOTH")
        push_channels = {
            NotificationService._channel_value("BOTH"),
            NotificationService._channel_value("PUSH"),
        }
        in_app_channel = NotificationService._channel_value("IN_APP")
        users_with_push_dispatch: set[int] = set()

        for profile in queryset.iterator():
            effective_channel = normalized_channel
            profile_user_id = getattr(profile, "user_id", None)
            if effective_channel in push_channels and profile_user_id is not None:
                if profile_user_id in users_with_push_dispatch:
                    effective_channel = in_app_channel
                else:
                    users_with_push_dispatch.add(profile_user_id)

            try:
                notification = NotificationService.emit(
                    profile=profile,
                    notification_type=notification_type,
                    title=title,
                    body=body,
                    data=data,
                    action_path=action_path,
                    channel=effective_channel,
                    dedupe_key=f"{dedupe_prefix}:{profile.id}",
                )
                notifications.append(notification)
                sent += 1
                if effective_channel in push_channels:
                    sent_push += 1
                else:
                    sent_in_app_only += 1
            except Exception:
                skipped += 1

        return {
            "sent": sent,
            "skipped": skipped,
            "total": sent + skipped,
            "sent_push": sent_push,
            "sent_in_app_only": sent_in_app_only,
            "notification_ids": [getattr(item, "id", None) for item in notifications],
        }
