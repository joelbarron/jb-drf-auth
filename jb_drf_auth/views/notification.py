from __future__ import annotations

from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from jb_drf_auth.conf import get_setting
from jb_drf_auth.serializers import (
    NotificationBroadcastSerializer,
    NotificationInboxSerializer,
    NotificationPushTokenUpsertSerializer,
    NotificationSendSerializer,
)
from jb_drf_auth.services.client import ClientService
from jb_drf_auth.services.notification_dispatch import NotificationDispatchService
from jb_drf_auth.utils import get_device_model_cls, get_notification_model_cls, get_profile_model_cls


BACKOFFICE_ROLES = {"ADMIN", "STAFF"}


def _is_backoffice_request(request) -> bool:
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return True

    auth_payload = request.auth or {}
    profile_claim = str(get_setting("PROFILE_ID_CLAIM") or "profile_id").strip() or "profile_id"
    profile_id = auth_payload.get(profile_claim) if hasattr(auth_payload, "get") else None
    if not profile_id:
        return False

    profile_model = get_profile_model_cls()
    profile = profile_model.objects.filter(id=profile_id, user=user).first()
    if not profile:
        return False
    role = str(getattr(profile, "role", "")).strip().upper()
    return role in BACKOFFICE_ROLES


class NotificationSendView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not _is_backoffice_request(request):
            return Response(
                {"detail": _("No tienes permisos para enviar notificaciones de prueba.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = NotificationSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        try:
            notification = NotificationDispatchService.send_to_profile(
                profile_id=payload["profile_id"],
                notification_type=payload["type"],
                title=payload["title"],
                body=payload.get("body") or "",
                data=payload.get("data") or {},
                action_path=payload.get("action_path"),
                channel=payload.get("channel"),
                dedupe_key=payload.get("dedupe_key"),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                "detail": "Notification sent.",
                "notification_id": getattr(notification, "id", None),
            },
            status=status.HTTP_200_OK,
        )


class NotificationBroadcastView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not _is_backoffice_request(request):
            return Response(
                {"detail": _("No tienes permisos para enviar notificaciones de prueba.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = NotificationBroadcastSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        result = NotificationDispatchService.broadcast(
            notification_type=payload["type"],
            title=payload["title"],
            body=payload.get("body") or "",
            data=payload.get("data") or {},
            action_path=payload.get("action_path"),
            channel=payload.get("channel"),
            dedupe_key_prefix=payload.get("dedupe_key_prefix"),
            profile_ids=payload.get("profile_ids"),
        )

        return Response(
            {
                "detail": "Broadcast dispatched.",
                **result,
            },
            status=status.HTTP_200_OK,
        )


class NotificationInboxViewSet(viewsets.ModelViewSet):
    """Inbox notifications for active profile."""

    serializer_class = NotificationInboxSerializer
    http_method_names = ["get", "head", "options", "post"]

    def get_permissions(self):
        return [IsAuthenticated()]

    @staticmethod
    def _has_field(model_cls, field_name: str) -> bool:
        return any(getattr(field, "name", "") == field_name for field in getattr(model_cls, "_meta").fields)

    def _get_active_profile(self):
        auth_payload = self.request.auth or {}
        profile_claim = str(get_setting("PROFILE_ID_CLAIM") or "profile_id").strip() or "profile_id"
        profile_id = auth_payload.get(profile_claim) if hasattr(auth_payload, "get") else None
        if not profile_id:
            raise ValidationError({"detail": _("Active profile is required.")})

        profile_model = get_profile_model_cls()
        profile = profile_model.objects.filter(id=profile_id, user=self.request.user).first()
        if not profile:
            raise ValidationError({"detail": _("Profile not found.")})
        return profile

    def get_queryset(self):
        notification_model = get_notification_model_cls()
        profile = self._get_active_profile()
        queryset = notification_model.objects.filter(profile=profile)
        if self._has_field(notification_model, "deleted"):
            queryset = queryset.filter(deleted__isnull=True)

        if self._has_field(notification_model, "sent_at"):
            queryset = queryset.order_by("-sent_at", "-id")
        else:
            queryset = queryset.order_by("-id")

        unread_only = str(self.request.query_params.get("unread", "")).strip().lower()
        if unread_only in {"1", "true", "yes"} and self._has_field(notification_model, "read_at"):
            queryset = queryset.filter(read_at__isnull=True)
        return queryset

    def retrieve(self, request, *args, **kwargs):
        return Response(
            {"detail": _("Retrieve operation is not allowed for notifications.")},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": _("Create operation is not allowed for notifications.")},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def update(self, request, *args, **kwargs):
        return Response(
            {"detail": _("Update operation is not allowed for notifications.")},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def partial_update(self, request, *args, **kwargs):
        return Response(
            {"detail": _("Update operation is not allowed for notifications.")},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": _("Delete operation is not allowed for notifications.")},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=True, methods=["POST"], url_path="read")
    def read(self, request, pk=None):
        notification = self.get_object()
        notification_model = get_notification_model_cls()
        if self._has_field(notification_model, "read_at") and getattr(notification, "read_at", None) is None:
            notification.read_at = timezone.now()
            update_fields = ["read_at"]
            if self._has_field(notification_model, "modified"):
                update_fields.append("modified")
            notification.save(update_fields=update_fields)

        serializer = self.get_serializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["POST"], url_path="read-all")
    def read_all(self, request, *args, **kwargs):
        notification_model = get_notification_model_cls()
        queryset = self.get_queryset()
        if self._has_field(notification_model, "read_at"):
            queryset = queryset.filter(read_at__isnull=True)
            now = timezone.now()
            update_kwargs = {"read_at": now}
            if self._has_field(notification_model, "modified"):
                update_kwargs["modified"] = now
            updated = queryset.update(**update_kwargs)
        else:
            updated = 0
        return Response({"updated": updated}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["GET"], url_path="unread-count")
    def unread_count(self, request, *args, **kwargs):
        notification_model = get_notification_model_cls()
        queryset = self.get_queryset()
        if self._has_field(notification_model, "read_at"):
            queryset = queryset.filter(read_at__isnull=True)
        count = queryset.count()
        return Response({"count": count}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["POST"], url_path="push-token")
    def push_token(self, request, *args, **kwargs):
        serializer = NotificationPushTokenUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        device_model = get_device_model_cls()
        device, _created = ClientService.upsert_mobile_device(
            device_model=device_model,
            user=request.user,
            token=payload["device_token"],
            platform=payload.get("platform") or "Unknown Platform",
            name=payload.get("name") or "Unknown Device",
            notification_token=payload.get("notification_token"),
        )
        return Response(
            {
                "detail": _("Push token updated successfully."),
                "device_id": getattr(device, "id", None),
                "notification_token": getattr(device, "notification_token", None),
            },
            status=status.HTTP_200_OK,
        )
