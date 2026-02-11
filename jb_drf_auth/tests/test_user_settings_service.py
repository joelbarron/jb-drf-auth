import os
import unittest
from unittest.mock import patch

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jb_drf_auth.tests.settings")
django.setup()

from jb_drf_auth.services.user_settings import UserSettingsService


class DummyUser:
    def __init__(self, settings=None):
        self.settings = settings if settings is not None else {}
        self.saved_with = None

    def save(self, update_fields=None):
        self.saved_with = update_fields


class DummyQuerySet:
    def __init__(self, users):
        self._users = users

    def iterator(self):
        return iter(self._users)


class DummyManager:
    def __init__(self, users):
        self._users = users

    def all(self):
        return DummyQuerySet(self._users)


class DummyUserModel:
    objects = None


class UserSettingsServiceTests(unittest.TestCase):
    def test_set_and_remove_user_setting(self):
        user = DummyUser(settings={"a": 1})

        UserSettingsService.set_user_setting(user, "b", 2)
        self.assertEqual(user.settings["b"], 2)
        self.assertEqual(user.saved_with, ["settings"])

        UserSettingsService.remove_user_setting(user, "a")
        self.assertNotIn("a", user.settings)

    def test_set_and_remove_user_feature(self):
        user = DummyUser(settings={})

        UserSettingsService.set_user_feature(user, "reports_beta", True)
        self.assertTrue(user.settings["custom_features_available"]["reports_beta"])

        UserSettingsService.remove_user_feature(user, "reports_beta")
        self.assertNotIn("reports_beta", user.settings["custom_features_available"])

    @patch("jb_drf_auth.services.user_settings.get_user_model")
    def test_set_all_users_feature(self, mock_get_user_model):
        users = [DummyUser(settings={}), DummyUser(settings={"custom_features_available": {}})]
        DummyUserModel.objects = DummyManager(users)
        mock_get_user_model.return_value = DummyUserModel

        updated = UserSettingsService.set_all_users_feature("new_dashboard", True)
        self.assertEqual(updated, 2)
        for user in users:
            self.assertTrue(user.settings["custom_features_available"]["new_dashboard"])

    @patch("jb_drf_auth.services.user_settings.get_user_model")
    def test_remove_all_users_setting(self, mock_get_user_model):
        users = [
            DummyUser(settings={"release_channel": "stable"}),
            DummyUser(settings={}),
        ]
        DummyUserModel.objects = DummyManager(users)
        mock_get_user_model.return_value = DummyUserModel

        updated = UserSettingsService.remove_all_users_setting("release_channel")
        self.assertEqual(updated, 1)
        self.assertNotIn("release_channel", users[0].settings)
