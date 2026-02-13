from jb_drf_auth.providers.base import BaseEmailProvider


class ConsoleEmailProvider(BaseEmailProvider):
    """
    Debug email provider that prints outgoing messages to stdout.
    """

    def send_email(self, to_email: str, subject: str, text_body: str, html_body: str | None = None):
        print(
            "[jb_drf_auth][email][console] "
            f"to={to_email} subject={subject} text_body={text_body} html_body={html_body}"
        )
        return {
            "provider": "console",
            "to_email": to_email,
            "subject": subject,
            "text_body": text_body,
            "html_body": html_body,
        }
