from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from jb_drf_auth.permissions import BootstrapTokenOrAdmin
from jb_drf_auth.serializers import UserAdminCreateSerializer
from jb_drf_auth.utils import get_profile_model_cls


User = get_user_model()


class CreateSuperUserView(APIView):
    permission_classes = [BootstrapTokenOrAdmin]

    def post(self, request):
        serializer = UserAdminCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if User.objects.filter(email=data["email"]).exists():
            return Response({"detail": _("El usuario ya existe.")}, status=status.HTTP_409_CONFLICT)

        user = User.objects.create_superuser(
            email=data["email"],
            password=data["password"],
            is_verified=True,
        )

        profile_model = get_profile_model_cls()
        profile_model.objects.create(
            user=user,
            role="ADMIN",
            is_active=True,
            is_default=True,
            gender="OTHER",
            first_name="Super",
            last_name_1="Admin",
            last_name_2="User",
        )

        return Response(
            {
                "detail": _("Superusuario creado."),
                "id": user.id,
                "email": user.email,
                "is_superuser": user.is_superuser,
                "is_staff": user.is_staff,
            },
            status=status.HTTP_201_CREATED,
        )


class CreateStaffUserView(APIView):
    permission_classes = [BootstrapTokenOrAdmin]

    def post(self, request):
        serializer = UserAdminCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if User.objects.filter(email=data["email"]).exists():
            return Response({"detail": _("El usuario ya existe.")}, status=status.HTTP_409_CONFLICT)

        user = User.objects.create_user(
            email=data["email"],
            password=data["password"],
            is_staff=True,
            is_verified=True,
        )

        profile_model = get_profile_model_cls()
        profile_model.objects.create(
            user=user,
            role="ADMIN",
            is_active=True,
            is_default=True,
            gender="OTHER",
            first_name="Staff",
            last_name_1="Admin",
            last_name_2="User",
        )

        return Response(
            {
                "detail": _("Usuario staff creado."),
                "id": user.id,
                "email": user.email,
                "is_superuser": user.is_superuser,
                "is_staff": user.is_staff,
            },
            status=status.HTTP_201_CREATED,
        )
