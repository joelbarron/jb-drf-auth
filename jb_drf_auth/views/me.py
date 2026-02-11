from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext as _

from jb_drf_auth.services.me import MeService


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        auth_payload = request.auth or {}
        profile_id = auth_payload.get("profile_id")
        client = request.query_params.get("client")
        device_token = request.query_params.get("device_token")

        if not profile_id:
            raise AuthenticationFailed(_("Falta perfil en el token"))

        if getattr(user, "deleted", None) or not getattr(user, "is_active", True) or not getattr(
            user, "is_verified", True
        ):
            return Response(
                {"detail": _("Usuario no valido, eliminado, inactivo o no verificado")},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        response = MeService.get_me(
            user=user,
            client=client,
            profile_id=profile_id,
            device_token=device_token,
        )

        return Response(response, status=status.HTTP_200_OK)
