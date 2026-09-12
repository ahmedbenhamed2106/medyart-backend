from rest_framework import permissions, status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.contrib.auth.models import User

# Safe model imports
try:
    from gallery.models import PhotoModel as Photo
except ImportError:
    try:
        from gallery.models import PhotoModel
        Photo = PhotoModel
    except ImportError:
        from gallery.models import Photo

from gallery.models import InteractionModel, CommentModel
from gallery.serializers import (
    PhotoSerializer,
    CommentSerializer,
    InteractionSerializer,
    UserRegisterSerializer
)


class PhotoViewSet(viewsets.ModelViewSet):
    queryset = Photo.objects.all().order_by('-created_at')
    serializer_class = PhotoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = CommentModel.objects.all().order_by('-updated_at')
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class InteractionViewSet(viewsets.ModelViewSet):
    queryset = InteractionModel.objects.all()
    serializer_class = InteractionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreatePaymentIntentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        return Response({
            "clientSecret": "mock_client_secret_demo",
            "message": "Payment intent created successfully."
        }, status=status.HTTP_200_OK)


class PhotoListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        photos = Photo.objects.all().order_by('-created_at')
        data = []
        for photo in photos:
            likes = photo.interactions.filter(vote='like').count()
            dislikes = photo.interactions.filter(vote='dislike').count()
            user_vote = None
            if request.user.is_authenticated:
                v = photo.interactions.filter(user=request.user).first()
                if v:
                    user_vote = v.vote

            comments = [{
                'id': c.id,
                'username': c.user.username,
                'text': c.text,
                'updated_at': c.updated_at
            } for c in photo.comments.all().order_by('-updated_at')]

            data.append({
                'id': photo.id,
                'title': photo.title,
                'image_url': photo.image.url if getattr(photo, 'image', None) else getattr(photo, 'image_url', ''),
                'likes': likes,
                'dislikes': dislikes,
                'user_vote': user_vote,
                'comments': comments,
                'owner': photo.user.username
            })
        return Response(data)

    def post(self, request):
        title = request.data.get('title', 'Untitled')
        image_file = request.FILES.get('image') or request.FILES.get('file')

        if not image_file:
            return Response({"detail": "An image file is required."}, status=status.HTTP_400_BAD_REQUEST)

        photo = Photo.objects.create(
            user=request.user,
            title=title,
            image=image_file
        )
        return Response({'id': photo.id, 'title': photo.title}, status=status.HTTP_201_CREATED)


class AccountUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        user = request.user
        action = request.data.get('action')

        if action == 'username':
            old_username = request.data.get('old_username')
            new_username = request.data.get('new_username')
            confirm_username = request.data.get('confirm_username')

            if user.username != old_username:
                return Response({"detail": "Current username does not match."}, status=status.HTTP_400_BAD_REQUEST)
            if new_username != confirm_username:
                return Response({"detail": "New usernames do not match."}, status=status.HTTP_400_BAD_REQUEST)
            
            user.username = new_username
            user.save()
            return Response({"message": "Username updated successfully."})

        elif action == 'password':
            old_password = request.data.get('old_password')
            new_password = request.data.get('new_password')
            confirm_password = request.data.get('confirm_password')

            if not user.check_password(old_password):
                return Response({"detail": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
            if new_password != confirm_password:
                return Response({"detail": "New passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.save()
            return Response({"message": "Password updated successfully."})

        elif action == 'card':
            card_number = request.data.get('card_number')
            exp_date = request.data.get('exp_date')
            cvc = request.data.get('cvc')

            if not (card_number and exp_date and cvc):
                return Response({"detail": "Please fill out all credit card fields."}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"message": "Credit card details saved successfully."})

        return Response({"detail": "Invalid action requested."}, status=status.HTTP_400_BAD_REQUEST)
