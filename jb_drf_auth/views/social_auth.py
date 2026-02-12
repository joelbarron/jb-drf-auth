import logging

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

logger = logging.getLogger("jb_drf_auth.views.social_auth")


class SocialLoginView(APIView):
    permission_classes = []
    throttle_classes = [BasicLoginIPThrottle, BasicLoginIdentityThrottle]

    def post(self, request):
        serializer = SocialLoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            payload = serializer.save()
        except SocialAuthError as exc:
            logger.warning(
                "social_login_failed provider=%s code=%s status=%s client=%s",
                serializer.validated_data.get("provider"),
                exc.code,
                exc.status_code,
                serializer.validated_data.get("client"),
            )
            return Response({"detail": str(exc), "code": exc.code}, status=exc.status_code)
        logger.info(
            "social_login_success provider=%s client=%s user_created=%s linked_existing_user=%s",
            serializer.validated_data.get("provider"),
            serializer.validated_data.get("client"),
            payload.get("user_created"),
            payload.get("linked_existing_user"),
        )
        return Response(payload, status=status.HTTP_200_OK)


class SocialLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SocialLinkSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            payload = serializer.save()
        except SocialAuthError as exc:
            logger.warning(
                "social_link_failed provider=%s code=%s status=%s user_id=%s",
                serializer.validated_data.get("provider"),
                exc.code,
                exc.status_code,
                getattr(request.user, "id", None),
            )
            return Response({"detail": str(exc), "code": exc.code}, status=exc.status_code)
        logger.info(
            "social_link_success provider=%s created=%s user_id=%s",
            serializer.validated_data.get("provider"),
            payload.get("created"),
            getattr(request.user, "id", None),
        )
        return Response(payload, status=status.HTTP_200_OK)


class SocialUnlinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SocialUnlinkSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            payload = serializer.save()
        except SocialAuthError as exc:
            logger.warning(
                "social_unlink_failed provider=%s code=%s status=%s user_id=%s",
                serializer.validated_data.get("provider"),
                exc.code,
                exc.status_code,
                getattr(request.user, "id", None),
            )
            return Response({"detail": str(exc), "code": exc.code}, status=exc.status_code)
        logger.info(
            "social_unlink_success provider=%s user_id=%s",
            serializer.validated_data.get("provider"),
            getattr(request.user, "id", None),
        )
        return Response(payload, status=status.HTTP_200_OK)
