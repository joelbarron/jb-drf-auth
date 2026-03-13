from __future__ import annotations

import inspect
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from django.db import models, transaction
from django.utils.module_loading import import_string
from django.utils.translation import gettext as _

from jb_drf_auth.conf import get_setting
from jb_drf_auth.utils import (
    get_device_model_cls,
    get_otp_model_cls,
    get_profile_model_cls,
    get_social_account_model_cls,
)


def _to_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _safe_max_length(model_instance, field_name: str, fallback: int) -> int:
    try:
        field = model_instance._meta.get_field(field_name)
        max_length = getattr(field, "max_length", None)
        if isinstance(max_length, int) and max_length > 0:
            return max_length
    except Exception:
        pass
    return fallback


def _truncate(value: str, max_length: int) -> str:
    if max_length <= 0:
        return value
    return value[:max_length]


@dataclass
class HandlerExecutionResult:
    blocked: bool = False
    code: str | None = None
    detail: str | None = None
    dependencies: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[Any] = field(default_factory=list)


class DeletionBlockedError(Exception):
    def __init__(
        self,
        *,
        code: str,
        detail: str,
        dependencies: list[dict[str, Any]] | None = None,
        warnings: list[Any] | None = None,
        status_code: int = 400,
    ):
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.dependencies = dependencies or []
        self.warnings = warnings or []
        self.status_code = status_code

    @property
    def payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "detail": self.detail,
        }
        if self.dependencies:
            payload["dependencies"] = self.dependencies
        if self.warnings:
            payload["warnings"] = self.warnings
        return payload


class AccountDeletionService:
    _PROTECTED_ON_DELETE = {
        models.PROTECT,
        getattr(models, "RESTRICT", object()),
    }

    @classmethod
    def delete_profile(cls, profile) -> dict[str, Any]:
        if getattr(profile, "is_default", False):
            raise DeletionBlockedError(
                code="profile_is_default",
                detail=_("No se puede eliminar el perfil predeterminado."),
            )

        is_active = bool(getattr(profile, "is_active", False))
        if is_active:
            has_other_active = (
                profile.__class__
                .objects.filter(user=profile.user, is_active=True)
                .exclude(pk=profile.pk)
                .exists()
            )
            if not has_other_active:
                raise DeletionBlockedError(
                    code="profile_is_last_active",
                    detail=_("No se puede eliminar el último perfil activo."),
                )

        handler_result = cls._run_handlers(
            setting_name="PROFILE_DELETION_HANDLERS",
            context={
                "profile": profile,
                "user": getattr(profile, "user", None),
                "operation": "profile_delete",
            },
        )
        if handler_result.blocked:
            raise DeletionBlockedError(
                code=handler_result.code or "dependency_blocked",
                detail=handler_result.detail
                or _("No se puede eliminar el perfil porque tiene dependencias activas."),
                dependencies=handler_result.dependencies,
                warnings=handler_result.warnings,
            )

        dependencies = cls._collect_protected_related_dependencies(profile)
        if dependencies:
            raise DeletionBlockedError(
                code="dependency_blocked",
                detail=_("No se puede eliminar el perfil porque tiene dependencias protegidas."),
                dependencies=dependencies,
                warnings=handler_result.warnings,
            )

        profile.delete()
        return {
            "status": "deleted",
            "detail": _("Perfil eliminado correctamente."),
            "warnings": handler_result.warnings,
        }

    @classmethod
    def delete_account(cls, user, *, confirmation: bool) -> dict[str, Any]:
        if not confirmation:
            raise DeletionBlockedError(
                code="confirmation_required",
                detail=_("Debe confirmar la eliminación de la cuenta."),
            )

        with transaction.atomic():
            handler_result = cls._run_handlers(
                setting_name="ACCOUNT_DELETION_HANDLERS",
                context={
                    "user": user,
                    "operation": "account_delete",
                },
            )
            if handler_result.blocked:
                raise DeletionBlockedError(
                    code=handler_result.code or "dependency_blocked",
                    detail=handler_result.detail
                    or _("No se puede eliminar la cuenta porque tiene dependencias activas."),
                    dependencies=handler_result.dependencies,
                    warnings=handler_result.warnings,
                )

            dependencies = cls._collect_protected_related_dependencies(user)
            if dependencies:
                raise DeletionBlockedError(
                    code="dependency_blocked",
                    detail=_("No se puede eliminar la cuenta porque existen dependencias protegidas."),
                    dependencies=dependencies,
                    warnings=handler_result.warnings,
                )

            warnings = list(handler_result.warnings)
            cls._revoke_account_access(user=user, warnings=warnings)
            cls._anonymize_profiles(user=user)
            cls._anonymize_user(user=user)
            cls._soft_delete_profiles(user=user)
            user.delete()

        return {
            "status": "closed",
            "anonymized": True,
            "warnings": warnings,
            "detail": _("Cuenta eliminada correctamente."),
        }

    @classmethod
    def _soft_delete_profiles(cls, user) -> None:
        profile_model = get_profile_model_cls()
        profiles_qs = profile_model.objects.filter(user=user)
        for profile in profiles_qs:
            profile.delete()

    @classmethod
    def _anonymize_profiles(cls, user) -> None:
        profile_model = get_profile_model_cls()
        manager = getattr(profile_model, "all_objects", profile_model.objects)
        profiles_qs = manager.filter(user=user)
        for profile in profiles_qs:
            update_fields: list[str] = []
            for field_name, value in (
                ("first_name", None),
                ("last_name_1", None),
                ("last_name_2", None),
                ("birthday", None),
                ("gender", None),
                ("label", ""),
                ("is_default", False),
                ("is_active", False),
                ("settings", {}),
            ):
                if hasattr(profile, field_name):
                    setattr(profile, field_name, value)
                    update_fields.append(field_name)
            if hasattr(profile, "picture"):
                profile.picture = None
                update_fields.append("picture")
            if update_fields:
                profile.save(update_fields=list(dict.fromkeys(update_fields)))

    @classmethod
    def _anonymize_user(cls, user) -> None:
        marker = uuid.uuid4().hex[:10]
        user_id = getattr(user, "pk", "x")
        update_fields: list[str] = []

        if hasattr(user, "email"):
            email_max = _safe_max_length(user, "email", 254)
            user.email = _truncate(
                f"deleted+{user_id}-{marker}@deleted.local",
                email_max,
            )
            update_fields.append("email")

        if hasattr(user, "username"):
            username_max = _safe_max_length(user, "username", 150)
            user.username = _truncate(f"deleted_user_{user_id}_{marker}", username_max)
            update_fields.append("username")

        if hasattr(user, "phone"):
            phone_max = _safe_max_length(user, "phone", 20)
            user.phone = _truncate(f"deleted-{user_id}-{marker}", phone_max)
            update_fields.append("phone")

        if hasattr(user, "is_active"):
            user.is_active = False
            update_fields.append("is_active")

        if hasattr(user, "is_verified"):
            user.is_verified = False
            update_fields.append("is_verified")

        if hasattr(user, "terms_and_conditions"):
            user.terms_and_conditions = None
            update_fields.append("terms_and_conditions")

        if hasattr(user, "settings"):
            user.settings = {}
            update_fields.append("settings")

        if hasattr(user, "set_unusable_password"):
            user.set_unusable_password()
            update_fields.append("password")

        if update_fields:
            user.save(update_fields=list(dict.fromkeys(update_fields)))

    @classmethod
    def _revoke_account_access(cls, *, user, warnings: list[Any]) -> None:
        for getter, label in (
            (get_device_model_cls, "devices"),
            (get_otp_model_cls, "otp"),
            (get_social_account_model_cls, "social_accounts"),
        ):
            try:
                model_cls = getter()
            except Exception:
                continue
            try:
                model_cls.objects.filter(user=user).delete()
            except Exception as exc:
                warnings.append(f"{label}:{exc}")

        try:
            from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

            OutstandingToken.objects.filter(user=user).delete()
        except Exception:
            # Token blacklist app is optional.
            pass

    @classmethod
    def _run_handlers(cls, *, setting_name: str, context: dict[str, Any]) -> HandlerExecutionResult:
        result = HandlerExecutionResult()
        for handler in cls._resolve_handlers(setting_name):
            handler_output = cls._invoke_handler(handler, context=context)
            normalized = cls._normalize_handler_output(handler_output)
            if normalized.blocked:
                result.blocked = True
            if normalized.code and not result.code:
                result.code = normalized.code
            if normalized.detail and not result.detail:
                result.detail = normalized.detail
            if normalized.dependencies:
                result.dependencies.extend(normalized.dependencies)
            if normalized.warnings:
                result.warnings.extend(normalized.warnings)
        return result

    @classmethod
    def _resolve_handlers(cls, setting_name: str) -> list[Callable[..., Any]]:
        configured = get_setting(setting_name)
        handlers: list[Callable[..., Any]] = []
        for item in _to_list(configured):
            if callable(item):
                handlers.append(item)
            elif isinstance(item, str) and item.strip():
                handlers.append(import_string(item.strip()))
        return handlers

    @classmethod
    def _invoke_handler(cls, handler: Callable[..., Any], *, context: dict[str, Any]) -> Any:
        signature = inspect.signature(handler)
        accepts_kwargs = any(
            param.kind == inspect.Parameter.VAR_KEYWORD
            for param in signature.parameters.values()
        )
        if accepts_kwargs:
            return handler(**context)

        kwargs = {
            key: value
            for key, value in context.items()
            if key in signature.parameters
        }
        if kwargs:
            return handler(**kwargs)

        if len(signature.parameters) == 1:
            param_name = next(iter(signature.parameters))
            if param_name in context:
                return handler(context[param_name])
            if "user" in context:
                return handler(context["user"])
            if "profile" in context:
                return handler(context["profile"])

        return handler()

    @classmethod
    def _normalize_handler_output(cls, output: Any) -> HandlerExecutionResult:
        if output is None:
            return HandlerExecutionResult()

        if isinstance(output, HandlerExecutionResult):
            return output

        if isinstance(output, str):
            return HandlerExecutionResult(warnings=[output])

        if isinstance(output, (list, tuple)):
            return HandlerExecutionResult(warnings=list(output))

        if isinstance(output, dict):
            dependencies = _to_list(output.get("dependencies"))
            warnings = _to_list(output.get("warnings"))
            detail = output.get("detail") or output.get("message")
            return HandlerExecutionResult(
                blocked=bool(output.get("blocked")),
                code=output.get("code"),
                detail=detail,
                dependencies=[item for item in dependencies if isinstance(item, dict)],
                warnings=warnings,
            )

        return HandlerExecutionResult()

    @classmethod
    def _collect_protected_related_dependencies(cls, instance) -> list[dict[str, Any]]:
        dependencies: list[dict[str, Any]] = []
        for relation in instance._meta.related_objects:
            field = getattr(relation, "field", None)
            remote_field = getattr(field, "remote_field", None)
            on_delete = getattr(remote_field, "on_delete", None)
            if on_delete not in cls._PROTECTED_ON_DELETE:
                continue

            accessor_name = relation.get_accessor_name()
            if not accessor_name:
                continue

            related_model = relation.related_model
            count = 0

            if relation.one_to_one:
                try:
                    related_obj = getattr(instance, accessor_name)
                    count = 1 if related_obj is not None else 0
                except related_model.DoesNotExist:
                    count = 0
            else:
                related_manager = getattr(instance, accessor_name, None)
                if related_manager is not None and hasattr(related_manager, "all"):
                    count = related_manager.all().count()

            if count <= 0:
                continue

            dependencies.append(
                {
                    "model": f"{related_model._meta.app_label}.{related_model.__name__}",
                    "field": getattr(field, "name", accessor_name),
                    "count": count,
                }
            )

        return dependencies
