import base64
import io
import qrcode
import pyotp
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.conf import settings

from .models import Photo, ModelProfile, InteractionModel, CommentModel, OrderModel
from .serializers import (
    UserSerializer, PhotoSerializer, InteractionSerializer, 
    CommentSerializer, OrderSerializer, ProfileSerializer
)

# 1. AUTH / USER REGISTRATION VIEW
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserSerializer

# 2. STRIPE / PAYMENT VIEW
class CreatePaymentIntentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        photo_id = request.data.get('photo_id')
        resolution = request.data.get('resolution')

        if not photo_id or not resolution:
            return Response({"detail": "Photo ID and resolution are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Mock Stripe Client Secret for Demo/Production integration
        return Response({
            "clientSecret": "mock_stripe_client_secret",
            "message": "Payment intent created successfully"
        }, status=status.HTTP_200_OK)

# 3. ROUTE VIEWSETS & PHOTO LIST/CREATE
class PhotoListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        photos = Photo.objects.all().order_by('-created_at')
        serializer = PhotoSerializer(photos, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        title = request.data.get('title', 'Untitled')
        image_file = request.FILES.get('file') or request.FILES.get('image')
        image_url = request.data.get('image_url')

        if not image_file and not image_url:
            return Response({"detail": "An image file or image URL is required."}, status=status.HTTP_400_BAD_REQUEST)

        photo = Photo.objects.create(
            user=request.user,
            title=title,
            image=image_file if image_file else None,
            image_url=image_url if image_url else (image_file.url if image_file else "/bg.jpeg")
        )
        serializer = PhotoSerializer(photo, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class PhotoViewSet(generics.RetrieveDestroyAPIView):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class InteractionViewSet(generics.ListCreateAPIView):
    queryset = InteractionModel.objects.all()
    serializer_class = InteractionSerializer
    permission_classes = [permissions.IsAuthenticated]

class CommentViewSet(generics.ListCreateAPIView):
    queryset = CommentModel.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class OrderViewSet(generics.ListCreateAPIView):
    queryset = OrderModel.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

# 4. ACCOUNT MANAGEMENT VIEW
class AccountUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        user = request.user
        new_username = request.data.get('username')
        new_email = request.data.get('email')
        new_password = request.data.get('password')

        if new_username:
            user.username = new_username
        if new_email:
            user.email = new_email
        if new_password:
            user.set_password(new_password)
            update_session_auth_hash(request, user)
        
        user.save()
        return Response({"message": "Account details updated successfully", "username": user.username})

# 5. TWO-FACTOR AUTHENTICATION VIEWS
class TwoFactorSetupView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile, _ = ModelProfile.objects.get_or_create(user=request.user)
        if not profile.two_factor_secret:
            profile.two_factor_secret = pyotp.random_base32()
            profile.save()

        secret = profile.two_factor_secret
        totp = pyotp.TOTP(secret)
        otp_auth_url = totp.provisioning_uri(name=request.user.email or request.user.username, issuer_name="MedyArt")

        img = qrcode.make(otp_auth_url)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        qr_64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        return Response({
            "secret": secret,
            "qr_code": f"data:image/png;base64,{qr_64}",
            "is_2fa_enabled": profile.is_2fa_enabled
        })

class TwoFactorVerifyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        otp_code = request.data.get('otp_code') or request.data.get('code')
        enable = request.data.get('enable', True)
        profile, _ = ModelProfile.objects.get_or_create(user=request.user)

        if not enable:
            profile.is_2fa_enabled = False
            profile.save()
            return Response({"message": "2FA disabled successfully", "is_2fa_enabled": False})

        secret = profile.two_factor_secret
        if not secret:
            return Response({"detail": "2FA not initialized"}, status=status.HTTP_400_BAD_REQUEST)

        totp = pyotp.TOTP(secret)
        if totp.verify(otp_code):
            profile.is_2fa_enabled = True
            profile.save()
            return Response({"message": "2FA successfully verified", "is_2fa_enabled": True})
        
        return Response({"detail": "Invalid OTP code"}, status=status.HTTP_400_BAD_REQUEST)
