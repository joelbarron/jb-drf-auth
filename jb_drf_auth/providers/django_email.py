from django.core.mail import EmailMultiAlternatives

from jb_drf_auth.conf import get_setting
from jb_drf_auth.providers.base import BaseEmailProvider


class DjangoEmailProvider(BaseEmailProvider):
    def send_email(self, to_email: str, subject: str, text_body: str, html_body: str | None = None):
        from_email = get_setting("DEFAULT_FROM_EMAIL")
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email,
            to=[to_email],
        )
        if html_body:
            message.attach_alternative(html_body, "text/html")
        message.send(fail_silently=False)
