import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jb_drf_auth.tests.settings")
django.setup()

from jb_drf_auth.services.profile_mirror import ProfileRoleMirrorService


def _fields(*names):
    return [SimpleNamespace(name=name) for name in names]


class ProfileRoleMirrorServiceTests(unittest.TestCase):
    def test_is_disabled_by_default(self):
        self.assertFalse(ProfileRoleMirrorService.is_enabled())

    @patch("jb_drf_auth.services.profile_mirror.get_setting")
    def test_counterpart_role_resolves_bidirectional_pairs(self, get_setting):
        get_setting.return_value = {
            "ENABLED": True,
            "ROLE_PAIRS": (("HOST", "GUEST"),),
            "SYNC_FIELDS": ("first_name",),
        }

        self.assertEqual(ProfileRoleMirrorService.counterpart_role("HOST"), "GUEST")
        self.assertEqual(ProfileRoleMirrorService.counterpart_role("guest"), "HOST")
        self.assertIsNone(ProfileRoleMirrorService.counterpart_role("ADMIN"))

    @patch("jb_drf_auth.services.profile_mirror.get_setting")
    def test_sync_fields_filter_unsafe_fields(self, get_setting):
        get_setting.return_value = {
            "ENABLED": True,
            "ROLE_PAIRS": (("HOST", "GUEST"),),
            "SYNC_FIELDS": (
                "first_name",
                "settings",
                "is_active",
                "role",
                "is_default",
                "user",
            ),
        }

        self.assertEqual(ProfileRoleMirrorService.get_sync_fields(), {"first_name"})

    def test_ensure_counterpart_reuses_existing_active_profile(self):
        source_profile = SimpleNamespace(user=SimpleNamespace(id=1), role="HOST")
        existing_counterpart = SimpleNamespace(id=77)
        fake_qs = MagicMock()

        with (
            patch.object(ProfileRoleMirrorService, "is_enabled", return_value=True),
            patch.object(ProfileRoleMirrorService, "counterpart_role", return_value="GUEST"),
            patch.object(ProfileRoleMirrorService, "_profiles_queryset", return_value=fake_qs),
            patch.object(
                ProfileRoleMirrorService, "_oldest_profile", return_value=existing_counterpart
            ),
        ):
            result = ProfileRoleMirrorService.ensure_counterpart(source_profile, create_missing=True)

        self.assertEqual(result, existing_counterpart)

    @patch("jb_drf_auth.services.profile_mirror.get_profile_model_cls")
    def test_ensure_counterpart_creates_missing_profile_without_duplicates(
        self,
        get_profile_model_cls,
    ):
        source_user = SimpleNamespace(id=1)
        source_profile = SimpleNamespace(user=source_user, role="HOST", first_name="Joel")
        created_counterpart = SimpleNamespace(id=81)
        profile_model = MagicMock()
        profile_model._meta.get_fields.return_value = _fields(
            "user",
            "role",
            "is_default",
            "is_active",
            "first_name",
            "picture",
        )
        profile_model.objects.create.return_value = created_counterpart
        get_profile_model_cls.return_value = profile_model

        with (
            patch.object(ProfileRoleMirrorService, "is_enabled", return_value=True),
            patch.object(ProfileRoleMirrorService, "counterpart_role", return_value="GUEST"),
            patch.object(ProfileRoleMirrorService, "_profiles_queryset", return_value=MagicMock()),
            patch.object(ProfileRoleMirrorService, "_oldest_profile", return_value=None),
            patch.object(ProfileRoleMirrorService, "get_sync_fields", return_value={"first_name", "picture"}),
            patch.object(ProfileRoleMirrorService, "_clone_picture") as clone_picture,
        ):
            result = ProfileRoleMirrorService.ensure_counterpart(source_profile, create_missing=True)

        self.assertEqual(result, created_counterpart)
        profile_model.objects.create.assert_called_once_with(
            user=source_user,
            role="GUEST",
            is_default=False,
            is_active=True,
            first_name="Joel",
        )
        clone_picture.assert_called_once_with(source_profile, created_counterpart)

    @patch("jb_drf_auth.services.profile_mirror.get_profile_model_cls")
    def test_sync_profile_updates_allowed_fields_and_clones_picture(self, get_profile_model_cls):
        source_profile = SimpleNamespace(
            role="HOST",
            first_name="Ana",
            last_name_1="Lopez",
        )
        target_profile = SimpleNamespace(id=44)

        profile_model = MagicMock()
        profile_model._meta.get_fields.return_value = _fields("first_name", "last_name_1", "picture")
        filtered = profile_model.objects.filter.return_value
        get_profile_model_cls.return_value = profile_model

        with (
            patch.object(ProfileRoleMirrorService, "is_enabled", return_value=True),
            patch.object(
                ProfileRoleMirrorService,
                "get_sync_fields",
                return_value={"first_name", "last_name_1", "picture"},
            ),
            patch.object(ProfileRoleMirrorService, "ensure_counterpart", return_value=target_profile),
            patch.object(ProfileRoleMirrorService, "_clone_picture") as clone_picture,
        ):
            result = ProfileRoleMirrorService.sync_profile(
                source_profile,
                changed_fields={"first_name", "picture"},
            )

        self.assertEqual(result, target_profile)
        profile_model.objects.filter.assert_called_once_with(id=44)
        filtered.update.assert_called_once_with(first_name="Ana")
        clone_picture.assert_called_once_with(source_profile, target_profile)

    def test_sync_profile_skips_when_guard_is_active(self):
        source_profile = SimpleNamespace(role="HOST")

        with patch.object(ProfileRoleMirrorService, "ensure_counterpart") as ensure_counterpart:
            with ProfileRoleMirrorService.guard():
                result = ProfileRoleMirrorService.sync_profile(source_profile, changed_fields={"first_name"})

        self.assertIsNone(result)
        ensure_counterpart.assert_not_called()

    def test_clone_picture_saves_independent_file(self):
        source_picture = MagicMock()
        source_picture.name = "avatar.png"
        source_picture.read.return_value = b"image-bytes"

        source_profile = SimpleNamespace(picture=source_picture)
        target_profile = SimpleNamespace(picture=MagicMock(), save=MagicMock())

        ProfileRoleMirrorService._clone_picture(source_profile, target_profile)

        self.assertTrue(target_profile.picture.save.called)
        filename = target_profile.picture.save.call_args.args[0]
        self.assertIn("-mirror-", filename)
        self.assertNotEqual(filename, "avatar.png")
        target_profile.save.assert_called_once_with(update_fields=["picture"])
