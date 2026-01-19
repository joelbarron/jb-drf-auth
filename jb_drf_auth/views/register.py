from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from jb_drf_auth.serializers import RegisterSerializer


class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {"detail": "Usuario creado. Revisa tu correo para verificar tu cuenta."},
                status=status.HTTP_201_CREATED,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            print(exc)
            return Response(
                {"detail": f"Error al crear el usuario. {str(exc)}"},
                status=status.HTTP_409_CONFLICT,
            )
