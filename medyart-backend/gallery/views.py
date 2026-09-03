from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from gallery.models import PhotoModel, InteractionModel, CommentModel
from gallery.serializers import (
    PhotoSerializer,
    InteractionSerializer,
    CommentSerializer,
    UserRegisterSerializer
)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegisterSerializer

class PhotoViewSet(viewsets.ModelViewSet):
    queryset = PhotoModel.objects.all().order_by('-created_at')
    serializer_class = PhotoSerializer

class CommentViewSet(viewsets.ModelViewSet):
    queryset = CommentModel.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class InteractionViewSet(viewsets.ModelViewSet):
    queryset = InteractionModel.objects.all()
    serializer_class = InteractionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        photo_id = request.data.get('photo')
        vote_type = request.data.get('vote')

        interaction, created = InteractionModel.objects.update_or_create(
            user=user,
            photo_id=photo_id,
            defaults={'vote': vote_type}
        )
        
        serializer = self.get_serializer(interaction)
        return Response(serializer.data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)
