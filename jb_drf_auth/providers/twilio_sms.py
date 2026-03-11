import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from jb_drf_auth.conf import get_setting
from jb_drf_auth.providers.base import BaseSmsProvider


class TwilioSmsProvider(BaseSmsProvider):
    def send_sms(self, phone_number: str, message: str):
        account_sid = get_setting("TWILIO_ACCOUNT_SID")
        auth_token = get_setting("TWILIO_AUTH_TOKEN")
        from_number = get_setting("TWILIO_FROM_NUMBER")
        messaging_service_sid = get_setting("TWILIO_MESSAGING_SERVICE_SID")

        if not account_sid or not auth_token:
            raise RuntimeError("Twilio account credentials are not configured.")
        if not from_number and not messaging_service_sid:
            raise RuntimeError(
                "Configure TWILIO_FROM_NUMBER or TWILIO_MESSAGING_SERVICE_SID."
            )

        payload = {
            "To": phone_number,
            "Body": message,
        }
        if messaging_service_sid:
            payload["MessagingServiceSid"] = messaging_service_sid
        else:
            payload["From"] = from_number

        endpoint = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        req = Request(
            endpoint,
            data=urlencode(payload).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        req.add_header("Authorization", f"Basic {self._build_basic_auth(account_sid, auth_token)}")
        try:
            with urlopen(req, timeout=10) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else {"status": response.status}
        except HTTPError as exc:
            error_payload = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Twilio delivery failed: {error_payload}") from exc
        except (URLError, TimeoutError) as exc:
            raise RuntimeError("Twilio delivery failed: network error.") from exc

    @staticmethod
    def _build_basic_auth(username: str, password: str) -> str:
        import base64

        raw = f"{username}:{password}".encode("utf-8")
        return base64.b64encode(raw).decode("ascii")
