from jb_drf_auth.conf import get_setting
from jb_drf_auth.services.client import ClientService
from jb_drf_auth.services.email_confirmation import EmailConfirmationService
from jb_drf_auth.services.login import LoginService
from jb_drf_auth.services.me import MeService
from jb_drf_auth.services.otp import OtpService
from jb_drf_auth.services.password_reset import PasswordResetService
from jb_drf_auth.services.register import RegisterService
from jb_drf_auth.services.tokens import TokensService

CLIENT_CHOICES = get_setting("CLIENT_CHOICES")

__all__ = [
    "CLIENT_CHOICES",
    "ClientService",
    "EmailConfirmationService",
    "LoginService",
    "MeService",
    "OtpService",
    "PasswordResetService",
    "RegisterService",
    "TokensService",
]
