from __future__ import annotations

from contextlib import contextmanager
from os.path import basename, splitext
from threading import local
from typing import Any, Iterable
from uuid import uuid4

from django.core.files.base import ContentFile

from jb_drf_auth.conf import get_setting
from jb_drf_auth.utils import get_profile_model_cls


_THREAD_STATE = local()


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "si", "sí", "on"}


class ProfileRoleMirrorService:
    """Dual-role profile mirror and autocure helpers.

    Behavior is fully opt-in through:
    JB_DRF_AUTH["PROFILE_ROLE_MIRROR"].
    """

    @staticmethod
    def _settings() -> dict[str, Any]:
        value = get_setting("PROFILE_ROLE_MIRROR")
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _normalize_role(value: Any) -> str:
        role = str(value or "").strip().upper()
        return role

    @staticmethod
    def _model_field_names(model_cls) -> set[str]:
        return {field.name for field in model_cls._meta.get_fields()}

    @classmethod
    def is_enabled(cls) -> bool:
        return _to_bool(cls._settings().get("ENABLED"), default=False)

    @classmethod
    def autocure_on_auth_events_enabled(cls) -> bool:
        return _to_bool(cls._settings().get("AUTOCURE_ON_AUTH_EVENTS"), default=True)

    @classmethod
    def get_sync_fields(cls) -> set[str]:
        raw_fields = cls._settings().get("SYNC_FIELDS") or ()
        if not isinstance(raw_fields, (list, tuple, set)):
            return set()
        normalized = {
            str(field or "").strip()
            for field in raw_fields
            if str(field or "").strip()
        }
        # Hard block system fields even if accidentally configured.
        normalized.discard("settings")
        normalized.discard("is_active")
        normalized.discard("role")
        normalized.discard("is_default")
        normalized.discard("user")
        return normalized

    @classmethod
    def _role_pair_map(cls) -> dict[str, str]:
        raw_pairs = cls._settings().get("ROLE_PAIRS") or ()
        if not isinstance(raw_pairs, (list, tuple, set)):
            return {}

        pair_map: dict[str, str] = {}
        for pair in raw_pairs:
            left = None
            right = None

            if isinstance(pair, dict):
                left = (
                    pair.get("left")
                    or pair.get("source")
                    or pair.get("primary")
                    or pair.get("from")
                )
                right = (
                    pair.get("right")
                    or pair.get("target")
                    or pair.get("secondary")
                    or pair.get("to")
                )
            elif isinstance(pair, (list, tuple)) and len(pair) >= 2:
                left, right = pair[0], pair[1]
            elif isinstance(pair, str):
                normalized = (
                    pair.replace("<->", ":")
                    .replace("->", ":")
                    .replace("|", ":")
                    .replace(",", ":")
                )
                chunks = [chunk.strip() for chunk in normalized.split(":") if chunk.strip()]
                if len(chunks) >= 2:
                    left, right = chunks[0], chunks[1]

            left_role = cls._normalize_role(left)
            right_role = cls._normalize_role(right)
            if not left_role or not right_role or left_role == right_role:
                continue

            pair_map[left_role] = right_role
            pair_map[right_role] = left_role

        return pair_map

    @classmethod
    def counterpart_role(cls, role: Any) -> str | None:
        return cls._role_pair_map().get(cls._normalize_role(role))

    @staticmethod
    def _guard_depth() -> int:
        return int(getattr(_THREAD_STATE, "profile_mirror_depth", 0) or 0)

    @classmethod
    def _guard_active(cls) -> bool:
        return cls._guard_depth() > 0

    @classmethod
    @contextmanager
    def guard(cls):
        current_depth = cls._guard_depth()
        _THREAD_STATE.profile_mirror_depth = current_depth + 1
        try:
            yield
        finally:
            next_depth = max(cls._guard_depth() - 1, 0)
            if next_depth == 0:
                if hasattr(_THREAD_STATE, "profile_mirror_depth"):
                    delattr(_THREAD_STATE, "profile_mirror_depth")
            else:
                _THREAD_STATE.profile_mirror_depth = next_depth

    @classmethod
    def _profiles_queryset(cls, *, user, role: str | None = None, active_only: bool = False):
        profile_model = get_profile_model_cls()
        field_names = cls._model_field_names(profile_model)
        queryset = profile_model.objects.filter(user=user)

        if "deleted" in field_names:
            queryset = queryset.filter(deleted=None)
        if role and "role" in field_names:
            queryset = queryset.filter(role=role)
        if active_only and "is_active" in field_names:
            queryset = queryset.filter(is_active=True)
        return queryset

    @classmethod
    def _oldest_profile(cls, queryset):
        field_names = cls._model_field_names(queryset.model)
        if "created" in field_names:
            return queryset.order_by("created", "id").first()
        return queryset.order_by("id").first()

    @classmethod
    def _clone_picture(cls, source_profile, target_profile) -> None:
        if not hasattr(source_profile, "picture") or not hasattr(target_profile, "picture"):
            return

        source_picture = getattr(source_profile, "picture", None)
        target_picture = getattr(target_profile, "picture", None)

        if not source_picture:
            if target_picture:
                try:
                    target_picture.delete(save=False)
                except Exception:
                    pass
            setattr(target_profile, "picture", None)
            target_profile.save(update_fields=["picture"])
            return

        source_name = getattr(source_picture, "name", "") or ""
        if not source_name:
            return

        payload = None
        try:
            source_picture.open("rb")
            payload = source_picture.read()
        except Exception:
            payload = None
        finally:
            try:
                source_picture.close()
            except Exception:
                pass

        if not payload:
            return

        base_name = basename(source_name)
        root, extension = splitext(base_name)
        extension = extension or ".jpg"
        mirrored_name = f"{root or 'profile'}-mirror-{uuid4().hex[:10]}{extension}"

        target_profile.picture.save(mirrored_name, ContentFile(payload), save=False)
        target_profile.save(update_fields=["picture"])

    @classmethod
    def ensure_counterpart(cls, source_profile, create_missing: bool = True):
        if not cls.is_enabled():
            return None

        source_user = getattr(source_profile, "user", None)
        if source_profile is None or source_user is None:
            return None

        target_role = cls.counterpart_role(getattr(source_profile, "role", None))
        if not target_role:
            return None

        target_queryset = cls._profiles_queryset(user=source_user, role=target_role, active_only=True)
        target_profile = cls._oldest_profile(target_queryset)
        if target_profile or not create_missing:
            return target_profile

        profile_model = get_profile_model_cls()
        field_names = cls._model_field_names(profile_model)
        sync_fields = cls.get_sync_fields()

        create_kwargs: dict[str, Any] = {"user": source_user}
        if "role" in field_names:
            create_kwargs["role"] = target_role
        if "is_default" in field_names:
            create_kwargs["is_default"] = False
        if "is_active" in field_names:
            create_kwargs["is_active"] = True

        for field_name in sorted(sync_fields):
            if field_name == "picture":
                continue
            if field_name in field_names and hasattr(source_profile, field_name):
                create_kwargs[field_name] = getattr(source_profile, field_name)

        with cls.guard():
            target_profile = profile_model.objects.create(**create_kwargs)
            if "picture" in sync_fields and "picture" in field_names:
                cls._clone_picture(source_profile, target_profile)

        return target_profile

    @classmethod
    def sync_profile(cls, source_profile, *, changed_fields: Iterable[str] | None = None):
        if not cls.is_enabled() or cls._guard_active():
            return None

        sync_fields = cls.get_sync_fields()
        if not sync_fields:
            return None

        if changed_fields is None:
            effective_fields = set(sync_fields)
        else:
            effective_fields = {
                str(field_name or "").strip()
                for field_name in changed_fields
                if str(field_name or "").strip() in sync_fields
            }
        if not effective_fields:
            return None

        target_profile = cls.ensure_counterpart(source_profile, create_missing=True)
        if not target_profile:
            return None

        profile_model = get_profile_model_cls()
        field_names = cls._model_field_names(profile_model)

        update_values: dict[str, Any] = {}
        for field_name in sorted(effective_fields):
            if field_name == "picture":
                continue
            if field_name not in field_names or not hasattr(source_profile, field_name):
                continue
            update_values[field_name] = getattr(source_profile, field_name)

        with cls.guard():
            if update_values:
                profile_model.objects.filter(id=target_profile.id).update(**update_values)
                for field_name, value in update_values.items():
                    setattr(target_profile, field_name, value)

            if "picture" in effective_fields and "picture" in field_names:
                cls._clone_picture(source_profile, target_profile)

        return target_profile

    @classmethod
    def autocure_for_profile(cls, profile):
        if not cls.is_enabled() or not cls.autocure_on_auth_events_enabled():
            return None
        return cls.ensure_counterpart(profile, create_missing=True)

