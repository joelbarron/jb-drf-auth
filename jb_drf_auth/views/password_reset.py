from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext as _

from jb_drf_auth.serializers import (
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
)
from jb_drf_auth.throttling import (
    PasswordResetConfirmIPThrottle,
    PasswordResetRequestIPThrottle,
    PasswordResetRequestIdentityThrottle,
)


class PasswordResetRequestView(APIView):
    permission_classes = []
    throttle_classes = [PasswordResetRequestIPThrottle, PasswordResetRequestIdentityThrottle]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email_sent = serializer.save()
        if email_sent is False:
            return Response(
                {
                    "detail": _("Solicitud recibida, pero el correo no fue enviado."),
                    "email_sent": False,
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "detail": _("Si el correo existe, se ha enviado un enlace de restablecimiento."),
                "email_sent": True,
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = []
    throttle_classes = [PasswordResetConfirmIPThrottle]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": _("Contrasena restablecida con exito.")}, status=status.HTTP_200_OK)


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": _("Contrasena actualizada con exito.")}, status=status.HTTP_200_OK)
