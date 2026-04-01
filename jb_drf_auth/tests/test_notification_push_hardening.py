import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jb_drf_auth.tests.settings")
django.setup()

from jb_drf_auth.services.notification_dispatch import NotificationDispatchService


class DummyProfileQuerySet:
    def __init__(self, profiles):
        self._profiles = list(profiles)

    def filter(self, **kwargs):
        profile_ids = kwargs.get("id__in")
        if profile_ids is None:
            return self
        allowed = {int(value) for value in profile_ids}
        return DummyProfileQuerySet(
            [profile for profile in self._profiles if int(getattr(profile, "id", 0)) in allowed]
        )

    def iterator(self):
        return iter(self._profiles)


class NotificationPushHardeningTests(unittest.TestCase):
    @patch("jb_drf_auth.services.notification_dispatch.NotificationService.emit")
    @patch("jb_drf_auth.services.notification_dispatch.NotificationService._channel_value")
    @patch.object(NotificationDispatchService, "_profile_queryset")
    def test_broadcast_dedupes_push_per_user(
        self,
        profile_queryset,
        channel_value,
        emit,
    ):
        channel_value.side_effect = lambda name: name
        profile_queryset.return_value = DummyProfileQuerySet(
            [
                SimpleNamespace(id=11, user_id=1),
                SimpleNamespace(id=12, user_id=1),
                SimpleNamespace(id=13, user_id=2),
            ]
        )
        emit.side_effect = [
            SimpleNamespace(id=1001),
            SimpleNamespace(id=1002),
            SimpleNamespace(id=1003),
        ]

        result = NotificationDispatchService.broadcast(
            notification_type="TEST",
            title="Test",
            channel="BOTH",
        )

        self.assertEqual(result["sent"], 3)
        self.assertEqual(result["skipped"], 0)
        self.assertEqual(result["sent_push"], 2)
        self.assertEqual(result["sent_in_app_only"], 1)
        self.assertEqual(result["notification_ids"], [1001, 1002, 1003])

        channels = [call.kwargs.get("channel") for call in emit.call_args_list]
        self.assertEqual(channels, ["BOTH", "IN_APP", "BOTH"])

    @patch("jb_drf_auth.services.notification_dispatch.NotificationService.emit")
    @patch("jb_drf_auth.services.notification_dispatch.NotificationService._channel_value")
    @patch.object(NotificationDispatchService, "_profile_queryset")
    def test_broadcast_in_app_channel_keeps_all_in_app(
        self,
        profile_queryset,
        channel_value,
        emit,
    ):
        channel_value.side_effect = lambda name: name
        profile_queryset.return_value = DummyProfileQuerySet(
            [
                SimpleNamespace(id=21, user_id=10),
                SimpleNamespace(id=22, user_id=10),
            ]
        )
        emit.side_effect = [SimpleNamespace(id=2001), SimpleNamespace(id=2002)]

        result = NotificationDispatchService.broadcast(
            notification_type="TEST",
            title="Test",
            channel="IN_APP",
        )

        self.assertEqual(result["sent_push"], 0)
        self.assertEqual(result["sent_in_app_only"], 2)
        channels = [call.kwargs.get("channel") for call in emit.call_args_list]
        self.assertEqual(channels, ["IN_APP", "IN_APP"])
