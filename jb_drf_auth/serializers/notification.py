from rest_framework import serializers


CHANNEL_CHOICES = (
    ("IN_APP", "In-app only"),
    ("PUSH", "Push only"),
    ("BOTH", "In-app + push"),
)


class NotificationSendSerializer(serializers.Serializer):
    profile_id = serializers.IntegerField(required=True, min_value=1)
    type = serializers.CharField(required=True, max_length=64)
    title = serializers.CharField(required=True, max_length=255)
    body = serializers.CharField(required=False, allow_blank=True, allow_null=True, default="")
    data = serializers.JSONField(required=False, default=dict)
    action_path = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        default=None,
        max_length=300,
    )
    channel = serializers.ChoiceField(
        required=False,
        choices=CHANNEL_CHOICES,
        default="BOTH",
    )
    dedupe_key = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        default=None,
        max_length=255,
    )


class NotificationBroadcastSerializer(serializers.Serializer):
    type = serializers.CharField(required=True, max_length=64)
    title = serializers.CharField(required=True, max_length=255)
    body = serializers.CharField(required=False, allow_blank=True, allow_null=True, default="")
    data = serializers.JSONField(required=False, default=dict)
    action_path = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        default=None,
        max_length=300,
    )
    channel = serializers.ChoiceField(
        required=False,
        choices=CHANNEL_CHOICES,
        default="BOTH",
    )
    dedupe_key_prefix = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        default=None,
        max_length=255,
    )
    profile_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=False,
    )


class NotificationInboxSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    type = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    body = serializers.CharField(read_only=True, allow_null=True)
    data = serializers.JSONField(read_only=True)
    action_path = serializers.CharField(read_only=True, allow_null=True, allow_blank=True)
    channel = serializers.CharField(read_only=True, allow_null=True, allow_blank=True)
    sent_at = serializers.DateTimeField(read_only=True, allow_null=True)
    read_at = serializers.DateTimeField(read_only=True, allow_null=True)
    is_read = serializers.SerializerMethodField()
    created = serializers.DateTimeField(read_only=True, allow_null=True)
    modified = serializers.DateTimeField(read_only=True, allow_null=True)

    def get_is_read(self, obj):
        return getattr(obj, "read_at", None) is not None


class NotificationPushTokenUpsertSerializer(serializers.Serializer):
    notification_token = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    device_token = serializers.CharField(required=True, allow_blank=False)
    platform = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    name = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_notification_token(self, value):
        token = str(value or "").strip()
        if not token:
            return None
        return token

    def validate_device_token(self, value):
        token = str(value or "").strip()
        if not token:
            raise serializers.ValidationError("device_token is required.")
        return token
