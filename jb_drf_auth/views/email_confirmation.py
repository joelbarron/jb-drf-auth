from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from jb_drf_auth.serializers import EmailConfirmationSerializer, ResendConfirmationEmailSerializer


class AccountConfirmEmailView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = EmailConfirmationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Correo verificado con éxito."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendConfirmationEmailView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = ResendConfirmationEmailSerializer(data=request.data)
        if serializer.is_valid():
            email_sent = serializer.save()
            if email_sent is False:
                return Response(
                    {
                        "detail": "Solicitud recibida, pero el correo no fue enviado.",
                        "email_sent": False,
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"detail": "Correo de verificación reenviado.", "email_sent": True},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
