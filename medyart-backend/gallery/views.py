from rest_framework.views import APIView
from rest_framework import viewsets, status, permissions, generics
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
import pyotp
import qrcode
import io
import base64

from .models import PhotoModel, InteractionModel, CommentModel, OrderModel, Profile
from .serializers import (
    UserRegisterSerializer, 
    CommentSerializer, 
    InteractionSerializer, 
    PhotoSerializer, 
    ProfileSerializer
)

# 1. AUTH / USER REGISTRATION VIEW
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserRegisterSerializer

# 2. STRIPE / PAYMENT VIEW
class CreatePaymentIntentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        photo_id = request.data.get('photo_id')
        resolution = request.data.get('resolution')

        if not photo_id or not resolution:
            return Response({"detail": "photo_id and resolution are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Basic placeholder logic for Stripe Integration
        return Response({
            "clientSecret": "mock_stripe_client_secret",
            "message": "Payment intent created successfully"
        }, status=status.HTTP_200_OK)

# 3. ROUTER VIEWSETS
class PhotoViewSet(viewsets.ModelViewSet):
    queryset = PhotoModel.objects.all().order_by('-created_at')
    serializer_class = PhotoSerializer

class CommentViewSet(viewsets.ModelViewSet):
    queryset = CommentModel.objects.all().order_by('-created_at')
    serializer_class = CommentSerializer

class InteractionViewSet(viewsets.ModelViewSet):
    queryset = InteractionModel.objects.all()
    serializer_class = InteractionSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = OrderModel.objects.all().order_by('-created_at')
    serializer_class = PhotoSerializer  # Default serializer fallback

# 4. CLASS-BASED VIEWS
class PhotoListCreateView(APIView):
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get(self, request):
        photos = PhotoModel.objects.all().order_by('-created_at')
        serializer = PhotoSerializer(photos, many=True)
        return Response(serializer.data)
        
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        title = request.data.get('title')
        image_url = request.data.get('image_url')

        if not title or not image_url:
            return Response({"detail": "Title and image_url are required"}, status=status.HTTP_400_BAD_REQUEST)

        photo = PhotoModel.objects.create(title=title, image_url=image_url)
        return Response(PhotoSerializer(photo).data, status=status.HTTP_201_CREATED)

# 5. ACCOUNT MANAGEMENT VIEW
class UpdateAccountView(APIView):
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

# 6. TWO-FACTOR AUTHENTICATION VIEWS
class TwoFactorSetupView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        qr_url = totp.provisioning_uri(name=request.user.email or request.user.username, issuer_name="MedyArt")
        
        img = qrcode.make(qr_url)
        buf = io.BytesIO()
        img.save(buf)
        qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        return Response({"secret": secret, "qr_code": f"data:image/png;base64,{qr_b64}"})

class TwoFactorVerifyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        otp_code = request.data.get('otp_code')
        secret = request.data.get('secret')
        totp = pyotp.TOTP(secret)

        if totp.verify(otp_code):
            profile, _ = Profile.objects.get_or_create(user=request.user)
            profile.two_factor_secret = secret
            profile.is_2fa_enabled = True
            profile.save()
            return Response({"message": "2FA successfully enabled!"})
        
        return Response({"detail": "Invalid OTP code"}, status=status.HTTP_400_BAD_REQUEST)
