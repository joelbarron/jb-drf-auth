from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext as _

from jb_drf_auth.conf import get_setting
from jb_drf_auth.services.email_confirmation import EmailConfirmationService
from jb_drf_auth.utils import get_profile_model_cls


User = get_user_model()


class RegisterService:
    @staticmethod
    def register_user(
        email,
        username,
        password,
        password_confirm,
        first_name,
        last_name_1,
        last_name_2,
        birthday,
        gender,
        role,
        terms_and_conditions_accepted,
    ):
        if password != password_confirm:
            raise ValueError(_("Las contraseñas no coinciden."))

        if User.objects.filter(email=email).exists():
            raise ValueError(_("El correo electrónico ya esta en uso."))
        if username and User.objects.filter(username=username).exists():
            raise ValueError(_("El nombre de usuario ya esta en uso."))

        user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            is_active=False,
        )
        if terms_and_conditions_accepted and hasattr(user, "terms_and_conditions"):
            user.terms_and_conditions = timezone.now()
            user.save(update_fields=["terms_and_conditions"])

        profile_model = get_profile_model_cls()
        profile_model.objects.create(
            user=user,
            first_name=first_name,
            last_name_1=last_name_1,
            last_name_2=last_name_2,
            birthday=birthday,
            gender=gender,
            role=role or get_setting("DEFAULT_PROFILE_ROLE"),
            is_default=True,
        )

        email_sent = EmailConfirmationService.send_verification_email(user, raise_on_fail=False)
        return user, email_sent
