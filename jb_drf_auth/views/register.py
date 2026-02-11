from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils.translation import gettext as _

from jb_drf_auth.serializers import RegisterSerializer
from jb_drf_auth.throttling import RegisterIPThrottle, RegisterIdentityThrottle


class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [RegisterIPThrottle, RegisterIdentityThrottle]

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            email_sent = getattr(serializer, "email_sent", True)
            if not email_sent:
                return Response(
                    {
                        "detail": _("Usuario creado, pero el correo no fue enviado."),
                        "email_sent": False,
                    },
                    status=status.HTTP_201_CREATED,
                )
            return Response(
                {"detail": _("Usuario creado. Revisa tu correo para verificar tu cuenta.")},
                status=status.HTTP_201_CREATED,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            print(exc)
            return Response(
                {"detail": _("Error al crear el usuario. %(error)s") % {"error": str(exc)}},
                status=status.HTTP_409_CONFLICT,
            )
