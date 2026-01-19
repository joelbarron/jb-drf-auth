from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_account(request):
    if request.data.get("confirmation"):
        user = request.user
        user.delete()
        return Response("Cuenta eliminada correctamente.", status=status.HTTP_200_OK)

    return Response(
        "Debe confirmar la eliminacion de la cuenta.",
        status=status.HTTP_400_BAD_REQUEST,
    )
