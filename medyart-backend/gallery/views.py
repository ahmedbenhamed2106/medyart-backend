from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
import pyotp
import qrcode
import io
import base64
from .models import PhotoModel, Profile# Ensure Profile model stores 2fa_secret & is_2fa_enabled
from .serializers import PhotoSerializer

# 1. FIX PHOTO UPLOAD (Handles Multipart Files cleanly)
class PhotoListCreateView(APIView):
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get(self, request):
        photos = Photo.objects.all().order_by('-created_at')
        serializer = PhotoSerializer(photos, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        title = request.data.get('title')
        image_file = request.FILES.get('image')

        if not title or not image_file:
            return Response({"detail": "Title and image file are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Save photo instance
        photo = Photo.objects.create(title=title, image=image_file, owner=request.user)
        return Response(PhotoSerializer(photo).data, status=status.HTTP_201_CREATED)

# 2. ACCOUNT MANAGEMENT VIEW
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

# 3. TWO-FACTOR AUTHENTICATION VIEWS
class TwoFactorSetupView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        qr_url = totp.provisioning_uri(name=request.user.email or request.user.username, issuer_name="MedyArt")
        
        # Generate QR Code Image
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
