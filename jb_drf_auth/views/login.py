from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from jb_drf_auth.serializers import (
    BasicLoginSerializer,
    MagicLinkConsumeSerializer,
    SwitchProfileSerializer,
)
from jb_drf_auth.services.login import LoginService
from jb_drf_auth.services.magic_link import MagicLinkService
from jb_drf_auth.throttling import BasicLoginIPThrottle, BasicLoginIdentityThrottle


class BasicLoginView(APIView):
    permission_classes = []
    throttle_classes = [BasicLoginIPThrottle, BasicLoginIdentityThrottle]

    def post(self, request):
        serializer = BasicLoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class SwitchProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SwitchProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = serializer.validated_data["profile"]
        client = serializer.validated_data["client"]
        device = serializer.validated_data.get("device", None)

        response = LoginService.switch_profile(request.user, profile, client, device)
        return Response(response, status=status.HTTP_200_OK)


class MagicLinkConsumeView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = MagicLinkConsumeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        payload = MagicLinkService.consume_token(
            token=data.get("token", ""),
            client=data.get("client", "web"),
            role=data.get("role"),
            device_data=data.get("device"),
        )
        if not payload:
            raise ValidationError({"detail": "No se pudo iniciar sesión con la liga proporcionada."})
        return Response(payload, status=status.HTTP_200_OK)
