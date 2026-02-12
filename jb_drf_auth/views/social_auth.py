from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from jb_drf_auth.exceptions import SocialAuthError
from jb_drf_auth.serializers.social_auth import (
    SocialLinkSerializer,
    SocialLoginSerializer,
    SocialUnlinkSerializer,
)
from jb_drf_auth.throttling import BasicLoginIPThrottle, BasicLoginIdentityThrottle


class SocialLoginView(APIView):
    permission_classes = []
    throttle_classes = [BasicLoginIPThrottle, BasicLoginIdentityThrottle]

    def post(self, request):
        serializer = SocialLoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            payload = serializer.save()
        except SocialAuthError as exc:
            return Response({"detail": str(exc), "code": exc.code}, status=exc.status_code)
        return Response(payload, status=status.HTTP_200_OK)


class SocialLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SocialLinkSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            payload = serializer.save()
        except SocialAuthError as exc:
            return Response({"detail": str(exc), "code": exc.code}, status=exc.status_code)
        return Response(payload, status=status.HTTP_200_OK)


class SocialUnlinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SocialUnlinkSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            payload = serializer.save()
        except SocialAuthError as exc:
            return Response({"detail": str(exc), "code": exc.code}, status=exc.status_code)
        return Response(payload, status=status.HTTP_200_OK)
