from dataclasses import dataclass, field


class BaseSmsProvider:
    def send_sms(self, phone_number: str, message: str):
        raise NotImplementedError


class BaseEmailProvider:
    def send_email(self, to_email: str, subject: str, text_body: str, html_body: str | None = None):
        raise NotImplementedError


@dataclass
class SocialIdentity:
    provider: str
    provider_user_id: str
    email: str | None = None
    email_verified: bool = False
    first_name: str | None = None
    last_name_1: str | None = None
    last_name_2: str | None = None
    picture_url: str | None = None
    raw_response: dict = field(default_factory=dict)


class BaseSocialProvider:
    def __init__(self, provider: str, provider_settings: dict | None = None):
        self.provider = provider
        self.provider_settings = provider_settings or {}

    def authenticate(self, payload: dict) -> SocialIdentity:
        raise NotImplementedError
