from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from jb_drf_auth.serializers import BasicLoginSerializer, SwitchProfileSerializer
from jb_drf_auth.services.login import LoginService


class BasicLoginView(APIView):
    permission_classes = []

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
