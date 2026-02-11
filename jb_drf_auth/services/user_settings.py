from django.contrib.auth import get_user_model


class UserSettingsService:
    FEATURE_BUCKET_KEY = "custom_features_available"

    @staticmethod
    def _as_dict(value):
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _save_user_settings(user, payload):
        user.settings = payload
        user.save(update_fields=["settings"])
        return user

    @classmethod
    def set_user_setting(cls, user, key, value):
        payload = cls._as_dict(getattr(user, "settings", None))
        payload[key] = value
        return cls._save_user_settings(user, payload)

    @classmethod
    def remove_user_setting(cls, user, key):
        payload = cls._as_dict(getattr(user, "settings", None))
        payload.pop(key, None)
        return cls._save_user_settings(user, payload)

    @classmethod
    def set_user_feature(cls, user, feature_key, enabled):
        payload = cls._as_dict(getattr(user, "settings", None))
        features = cls._as_dict(payload.get(cls.FEATURE_BUCKET_KEY))
        features[feature_key] = bool(enabled)
        payload[cls.FEATURE_BUCKET_KEY] = features
        return cls._save_user_settings(user, payload)

    @classmethod
    def remove_user_feature(cls, user, feature_key):
        payload = cls._as_dict(getattr(user, "settings", None))
        features = cls._as_dict(payload.get(cls.FEATURE_BUCKET_KEY))
        features.pop(feature_key, None)
        payload[cls.FEATURE_BUCKET_KEY] = features
        return cls._save_user_settings(user, payload)

    @classmethod
    def set_all_users_setting(cls, key, value, queryset=None):
        user_model = get_user_model()
        users = queryset if queryset is not None else user_model.objects.all()
        updated = 0
        for user in users.iterator():
            payload = cls._as_dict(getattr(user, "settings", None))
            payload[key] = value
            user.settings = payload
            user.save(update_fields=["settings"])
            updated += 1
        return updated

    @classmethod
    def remove_all_users_setting(cls, key, queryset=None):
        user_model = get_user_model()
        users = queryset if queryset is not None else user_model.objects.all()
        updated = 0
        for user in users.iterator():
            payload = cls._as_dict(getattr(user, "settings", None))
            if key in payload:
                payload.pop(key, None)
                user.settings = payload
                user.save(update_fields=["settings"])
                updated += 1
        return updated

    @classmethod
    def set_all_users_feature(cls, feature_key, enabled, queryset=None):
        user_model = get_user_model()
        users = queryset if queryset is not None else user_model.objects.all()
        updated = 0
        for user in users.iterator():
            payload = cls._as_dict(getattr(user, "settings", None))
            features = cls._as_dict(payload.get(cls.FEATURE_BUCKET_KEY))
            features[feature_key] = bool(enabled)
            payload[cls.FEATURE_BUCKET_KEY] = features
            user.settings = payload
            user.save(update_fields=["settings"])
            updated += 1
        return updated

    @classmethod
    def remove_all_users_feature(cls, feature_key, queryset=None):
        user_model = get_user_model()
        users = queryset if queryset is not None else user_model.objects.all()
        updated = 0
        for user in users.iterator():
            payload = cls._as_dict(getattr(user, "settings", None))
            features = cls._as_dict(payload.get(cls.FEATURE_BUCKET_KEY))
            if feature_key in features:
                features.pop(feature_key, None)
                payload[cls.FEATURE_BUCKET_KEY] = features
                user.settings = payload
                user.save(update_fields=["settings"])
                updated += 1
        return updated
