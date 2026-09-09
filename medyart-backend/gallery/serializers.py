from rest_framework import serializers
from django.contrib.auth.models import User
from gallery.models import PhotoModel, InteractionModel, CommentModel, Profile

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        # Auto-set username to email if not explicitly provided
        email = validated_data.get('email', '')
        username = validated_data.get('username') or email
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=validated_data['password']
        )
        return user

class CommentSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = CommentModel
        fields = ['id', 'user', 'photo', 'text', 'created_at']

class InteractionSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = InteractionModel
        fields = ['id', 'user', 'photo', 'vote', 'created_at']

class PhotoSerializer(serializers.ModelSerializer):
    likes_count = serializers.SerializerMethodField()
    dislikes_count = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = PhotoModel
        fields = ['id', 'title', 'image_url', 'created_at', 'likes_count', 'dislikes_count', 'comments']

    def get_likes_count(self, obj):
        return obj.interactions.filter(vote='like').count()

    def get_dislikes_count(self, obj):
        return obj.interactions.filter(vote='dislike').count()

class ProfileSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = Profile
        fields = ['id', 'user', 'is_2fa_enabled']
