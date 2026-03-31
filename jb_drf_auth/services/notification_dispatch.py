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
        notifications = []
        timestamp_seed = int(time.time() * 1000)
        dedupe_prefix = (dedupe_key_prefix or "").strip() or f"broadcast:{timestamp_seed}"

        for profile in queryset.iterator():
            try:
                notification = NotificationService.emit(
                    profile=profile,
                    notification_type=notification_type,
                    title=title,
                    body=body,
                    data=data,
                    action_path=action_path,
                    channel=channel,
                    dedupe_key=f"{dedupe_prefix}:{profile.id}",
                )
                notifications.append(notification)
                sent += 1
            except Exception:
                skipped += 1

        return {
            "sent": sent,
            "skipped": skipped,
            "total": sent + skipped,
            "notification_ids": [getattr(item, "id", None) for item in notifications],
        }
