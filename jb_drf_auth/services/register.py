from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _

from jb_drf_auth.services.account_provisioning import AccountProvisioningService


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

        result = AccountProvisioningService.provision_account(
            email=email,
            username=username,
            password=password,
            is_active=False,
            role=role,
            profile_data={
                "first_name": first_name,
                "last_name_1": last_name_1,
                "last_name_2": last_name_2,
                "birthday": birthday,
                "gender": gender,
            },
            terms_and_conditions_accepted=terms_and_conditions_accepted,
            send_verification=True,
            verification_channel="email",
            allow_verification_fallback=False,
            verification_raise_on_fail=False,
        )
        user = result["user"]

        email_sent = bool(result.get("verification", {}).get("sent"))
        return user, email_sent
