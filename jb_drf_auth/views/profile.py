from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext as _

from jb_drf_auth.serializers import ProfilePictureUpdateSerializer, ProfileSerializer
from jb_drf_auth.utils import get_profile_model_cls


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = get_profile_model_cls().objects.all()
    search_fields = ["id", "first_name", "last_name_1", "last_name_2"]
    filter_fields = ["is_active"]

    def get_serializer_class(self, *args, **kwargs):
        serializer_class = ProfileSerializer
        if self.request.method in ["PATCH", "POST", "PUT"]:
            serializer_class.Meta.depth = 0
        else:
            serializer_class.Meta.depth = 1
        return serializer_class

    def get_permissions(self):
        permissions = [IsAuthenticated]
        return [perm() for perm in permissions]

    def get_queryset(self):
        return get_profile_model_cls().objects.filter(user=self.request.user)


class ProfilePictureUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = ProfilePictureUpdateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        return Response(
            {
                "detail": _("Foto de perfil actualizada correctamente."),
                "profile_id": profile.id,
            },
            status=status.HTTP_200_OK,
        )
