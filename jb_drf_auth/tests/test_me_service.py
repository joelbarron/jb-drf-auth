from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from jb_drf_auth.services.me import MeService


class TestMeService(TestCase):
    @patch("jb_drf_auth.services.me.get_setting")
    def test_web_role_is_resolved_from_profile_role_choices(self, get_setting):
        get_setting.return_value = (
            ("ADMIN", "Admin"),
            ("DOCTOR", "Doctor"),
            ("PATIENT", "Patient"),
            ("STAFF", "Staff"),
        )
        self.assertEqual(MeService._web_role_from_profile(SimpleNamespace(role="ADMIN")), ["admin"])
        self.assertEqual(MeService._web_role_from_profile(SimpleNamespace(role="DOCTOR")), ["doctor"])
        self.assertEqual(MeService._web_role_from_profile(SimpleNamespace(role="PATIENT")), ["patient"])
        self.assertEqual(MeService._web_role_from_profile(SimpleNamespace(role="STAFF")), ["staff"])

    @patch("jb_drf_auth.services.me.get_setting")
    def test_web_role_uses_lowercase_fallback_for_unknown_roles(self, get_setting):
        get_setting.return_value = (("ADMIN", "Admin"),)
        self.assertEqual(MeService._web_role_from_profile(SimpleNamespace(role="STAFF")), ["staff"])

    @patch("jb_drf_auth.services.me.ProfileSerializer")
    def test_get_me_web_uses_profile_role_mapping(self, profile_serializer_cls):
        user = SimpleNamespace(email="doctor@example.com", phone="+5215512345678", username="doctor")
        profile = SimpleNamespace(
            role="DOCTOR",
            display_name="Doctor Test",
            full_name="Doctor Test",
            birthday=None,
            picture=None,
            settings={},
        )
        profile_serializer_cls.return_value.data = {"id": 7, "role": "DOCTOR"}

        payload = MeService.get_me_web(user=user, profile=profile, tokens=None)

        self.assertEqual(payload["user"]["role"], ["doctor"])
        self.assertEqual(payload["active_profile"]["role"], "DOCTOR")
        self.assertEqual(payload["user"]["data"]["phone"], "+5215512345678")
