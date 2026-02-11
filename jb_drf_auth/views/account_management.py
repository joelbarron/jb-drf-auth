from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext as _

from jb_drf_auth.serializers import UserSerializer, UserUpdateSerializer

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_account(request):
    if request.data.get("confirmation"):
        user = request.user
        user.delete()
        return Response(_("Cuenta eliminada correctamente."), status=status.HTTP_200_OK)

    return Response(
        _("Debe confirmar la eliminacion de la cuenta."),
        status=status.HTTP_400_BAD_REQUEST,
    )


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
