import base64
import io
import qrcode
import pyotp
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.contrib.auth.models import User
from django.db.models import Count, Q

from .models import Photo, ModelProfile, InteractionModel, CommentModel

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
                'user_id': c.user.id,
                'text': c.text,
                'updated_at': c.updated_at
            } for c in photo.comments.all().order_by('-updated_at')]

            data.append({
                'id': photo.id,
                'title': photo.title,
                'image_url': photo.image.url if photo.image else photo.image_url,
                'likes': likes,
                'dislikes': dislikes,
                'user_vote': user_vote,
                'comments': comments,
                'owner': photo.user.username
            })
        return Response(data)

    def post(self, request):
        title = request.data.get('title', 'Untitled')
        image_file = request.FILES.get('file') or request.FILES.get('image')
        image_url = request.data.get('image_url')

        if not image_file and not image_url:
            return Response({"detail": "An image file or image URL is required."}, status=400)

        photo = Photo.objects.create(
            user=request.user,
            title=title,
            image=image_file if image_file else None,
            image_url=image_url if image_url else ""
        )
        return Response({'id': photo.id, 'title': photo.title}, status=201)

class VoteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, photo_id):
        vote_type = request.data.get('vote') # 'like' or 'dislike'
        if vote_type not in ['like', 'dislike']:
            return Response({'detail': 'Invalid vote type'}, status=400)

        existing = InteractionModel.objects.filter(user=request.user, photo_id=photo_id).first()
        if existing:
            if existing.vote == vote_type:
                existing.delete() # Toggle off
            else:
                existing.vote = vote_type
                existing.save()
        else:
            InteractionModel.objects.create(user=request.user, photo_id=photo_id, vote=vote_type)

        return Response({'message': 'Vote updated'})

class CommentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, photo_id):
        text = request.data.get('text', '').strip()
        if not text:
            return Response({'detail': 'Comment cannot be empty'}, status=400)

        comment, created = CommentModel.objects.update_or_create(
            user=request.user, photo_id=photo_id,
            defaults={'text': text}
        )
        return Response({'message': 'Comment saved', 'created': created})

class AccountUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        user = request.user
        action = request.data.get('action') # 'username', 'email', 'password', 'card'

        if action == 'username':
            user.username = request.data.get('username')
            user.save()
        elif action == 'email':
            user.email = request.data.get('email')
            user.save()
        elif action == 'password':
            user.set_password(request.data.get('password'))
            user.save()
        elif action == 'card':
            profile, _ = ModelProfile.objects.get_or_create(user=user)
            profile.card_last4 = request.data.get('card_last4', '4242')
            profile.card_brand = request.data.get('card_brand', 'Visa')
            profile.save()

        return Response({'message': 'Updated successfully', 'username': user.username})
