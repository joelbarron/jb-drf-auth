from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from jb_drf_auth.serializers import OtpCodeRequestSerializer, OtpCodeVerifySerializer
from jb_drf_auth.services.otp import OtpService


class RequestOtpCodeView(APIView):
    def post(self, request):
        serializer = OtpCodeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        response = OtpService.request_otp_code(data)
        return Response(response, status=status.HTTP_201_CREATED)


class VerifyOtpCodeView(APIView):
    def post(self, request):
        serializer = OtpCodeVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        response = OtpService.verify_otp_code(data)
        return Response(response, status=status.HTTP_200_OK)
