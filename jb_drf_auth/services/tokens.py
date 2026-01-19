from rest_framework_simplejwt.tokens import RefreshToken

from jb_drf_auth.conf import get_setting


class TokensService:
    @staticmethod
    def get_tokens_for_user(user, profile):
        if not profile:
            raise ValueError(
                "Se debe proporcionar un perfil valido para el usuario para generar tokens."
            )

        refresh = RefreshToken.for_user(user)
        refresh[get_setting("PROFILE_ID_CLAIM")] = profile.id
        return {
            "refreshToken": str(refresh),
            "accessToken": str(refresh.access_token),
        }
