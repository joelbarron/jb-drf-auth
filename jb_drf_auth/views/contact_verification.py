from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import AuthenticationFailed

from jb_drf_auth.serializers import (
    ContactVerificationRequestSerializer,
    ContactVerificationVerifySerializer,
)
from jb_drf_auth.services.contact_verification import ContactVerificationService


class ContactVerificationRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ContactVerificationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        payload = ContactVerificationService.request_verification(
            email=data.get("email"),
            phone=data.get("phone"),
            channel=data.get("channel"),
        )
        return Response(payload, status=status.HTTP_201_CREATED)


class ContactVerificationVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ContactVerificationVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user_id = request.user.id if request.user and request.user.is_authenticated else None
        try:
            payload = ContactVerificationService.verify_code_and_issue_proof(
                user_id=user_id,
                code=data.get("code"),
                channel=data.get("channel"),
                email=data.get("email"),
                phone=data.get("phone"),
            )
        except AuthenticationFailed as exc:
            raise ValidationError({"code": str(exc)})
        return Response(payload, status=status.HTTP_200_OK)
