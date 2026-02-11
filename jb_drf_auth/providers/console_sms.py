from jb_drf_auth.providers.base import BaseSmsProvider


class ConsoleSmsProvider(BaseSmsProvider):
    """
    Debug SMS provider that prints outgoing messages to stdout.
    """

    def send_sms(self, phone_number: str, message: str):
        print(f"[jb_drf_auth][sms][console] to={phone_number} message={message}")
        return {"provider": "console", "phone_number": phone_number, "message": message}
