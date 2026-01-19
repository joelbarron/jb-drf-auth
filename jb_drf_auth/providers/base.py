class BaseSmsProvider:
    def send_sms(self, phone_number: str, message: str):
        raise NotImplementedError


class BaseEmailProvider:
    def send_email(self, to_email: str, subject: str, text_body: str, html_body: str | None = None):
        raise NotImplementedError
