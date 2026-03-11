from rest_framework import serializers


class SocialAccountSerializer(serializers.Serializer):
    provider = serializers.CharField()
    email = serializers.EmailField(allow_null=True, required=False)
    email_verified = serializers.BooleanField(required=False)
    linked_at = serializers.SerializerMethodField()
    last_login_at = serializers.DateTimeField(allow_null=True, required=False)
    picture_url = serializers.URLField(allow_null=True, required=False)

    def get_linked_at(self, obj):
        return getattr(obj, "linked_at", None) or getattr(obj, "created", None)
