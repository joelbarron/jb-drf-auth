from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from jb_drf_auth.serializers import OtpCodeRequestSerializer, OtpCodeVerifySerializer
from jb_drf_auth.services.otp import OtpService
from jb_drf_auth.throttling import (
    OtpRequestIPThrottle,
    OtpRequestIdentityThrottle,
    OtpVerifyIPThrottle,
    OtpVerifyIdentityThrottle,
)


class RequestOtpCodeView(APIView):
    throttle_classes = [OtpRequestIPThrottle, OtpRequestIdentityThrottle]

    def post(self, request):
        serializer = OtpCodeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        response = OtpService.request_otp_code(data)
        return Response(response, status=status.HTTP_201_CREATED)


class VerifyOtpCodeView(APIView):
    throttle_classes = [OtpVerifyIPThrottle, OtpVerifyIdentityThrottle]

    def post(self, request):
        serializer = OtpCodeVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        response = OtpService.verify_otp_code(data)
        return Response(response, status=status.HTTP_200_OK)
