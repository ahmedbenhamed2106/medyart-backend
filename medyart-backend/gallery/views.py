import os
import stripe
from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from gallery.models import PhotoModel, InteractionModel, CommentModel, OrderModel
from gallery.serializers import (
    PhotoSerializer,
    InteractionSerializer,
    CommentSerializer,
    UserRegisterSerializer
)

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_dummy_key')

PRICING_TIERS = {
    'HD': 300,       # $3.00 in cents
    '1080P': 500,    # $5.00 in cents
    '1440P': 700,    # $7.00 in cents
    '4K': 900,       # $9.00 in cents
    '8K': 1200,      # $12.00 in cents
}

class CreatePaymentIntentView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        photo_id = request.data.get('photo_id')
        resolution = request.data.get('resolution', '').upper()

        if resolution not in PRICING_TIERS:
            return Response({'error': 'Invalid resolution tier'}, status=status.HTTP_400_BAD_REQUEST)

        amount_cents = PRICING_TIERS[resolution]

        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency='usd',
                metadata={'user_id': request.user.id, 'photo_id': photo_id, 'resolution': resolution}
            )

            OrderModel.objects.create(
                user=request.user,
                photo_id=photo_id,
                resolution=resolution,
                amount=amount_cents / 100,
                stripe_intent_id=intent['id']
            )

            return Response({'clientSecret': intent['client_secret']}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
