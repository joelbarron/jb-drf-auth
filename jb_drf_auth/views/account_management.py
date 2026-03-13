from django.contrib.auth import get_user_model
from django.core.exceptions import FieldError
from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from jb_drf_auth.serializers import (
    EmailAvailabilitySerializer,
    PhoneAvailabilitySerializer,
    SocialAccountSerializer,
    UserSerializer,
    UserUpdateSerializer,
    UsernameAvailabilitySerializer,
)
from jb_drf_auth.services.account_deletion import (
    AccountDeletionService,
    DeletionBlockedError,
)
from jb_drf_auth.utils import get_social_account_model_cls


def _is_truthy(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "si", "sí"}


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_account(request):
    try:
        payload = AccountDeletionService.delete_account(
            request.user,
            confirmation=_is_truthy(request.data.get("confirmation")),
        )
        return Response(payload, status=status.HTTP_200_OK)
    except DeletionBlockedError as exc:
        return Response(exc.payload, status=exc.status_code)


class AccountUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = UserUpdateSerializer(instance=request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = UserUpdateSerializer(instance=request.user, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)


class _BaseAvailabilityView(APIView):
    permission_classes = [AllowAny]
    serializer_class = None
    field_name = None

    def get(self, request):
        serializer = self.serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        value = serializer.validated_data[self.field_name]
        user_model = get_user_model()
        try:
            queryset = user_model.objects.filter(**{self.field_name: value})
        except FieldError:
            return Response(
                {"detail": _("Este tipo de disponibilidad no está soportado para este proyecto.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        current_user = getattr(request, "user", None)
        if getattr(current_user, "is_authenticated", False) and getattr(current_user, "pk", None):
            queryset = queryset.exclude(pk=current_user.pk)

        available = not queryset.exists()
        payload = {
            "field": self.field_name,
            "value": value,
            "available": available,
        }
        if not available:
            if self.field_name == "email":
                payload["detail"] = _("Ya existe un usuario con este correo.")
            elif self.field_name == "phone":
                payload["detail"] = _("Ya existe un usuario con este teléfono.")
            elif self.field_name == "username":
                payload["detail"] = _("El nombre de usuario ya está en uso.")
        return Response(payload, status=status.HTTP_200_OK)


class UsernameAvailabilityView(_BaseAvailabilityView):
    serializer_class = UsernameAvailabilitySerializer
    field_name = "username"


class EmailAvailabilityView(_BaseAvailabilityView):
    serializer_class = EmailAvailabilitySerializer
    field_name = "email"


class PhoneAvailabilityView(_BaseAvailabilityView):
    serializer_class = PhoneAvailabilitySerializer
    field_name = "phone"


class AccountSocialAccountsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        social_account_model = get_social_account_model_cls()
        queryset = social_account_model.objects.filter(user=request.user).order_by("provider", "-created")
        payload = SocialAccountSerializer(queryset, many=True).data
        return Response(payload, status=status.HTTP_200_OK)
