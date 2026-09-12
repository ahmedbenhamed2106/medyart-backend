from rest_framework import serializers
from django.contrib.auth.models import User
from gallery.models import InteractionModel, CommentModel

# Import PhotoModel/Photo and Profile with safe fallbacks
try:
    from gallery.models import PhotoModel as Photo
except ImportError:
    try:
        from gallery.models import PhotoModel
        Photo = PhotoModel
    except ImportError:
        from gallery.models import Photo

try:
    from gallery.models import Profile
except ImportError:
    try:
        from gallery.models import ModelProfile as Profile
    except ImportError:
        Profile = None


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        email = validated_data.get('email', '')
        username = validated_data.get('username') or email
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=validated_data['password']
        )
        return user


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = CommentModel
        fields = ['id', 'user', 'photo', 'text', 'created_at']


class InteractionSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = InteractionModel
        fields = ['id', 'user', 'photo', 'vote', 'created_at']


class PhotoSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    likes_count = serializers.SerializerMethodField()
    dislikes_count = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Photo
        fields = ['id', 'user', 'title', 'image', 'image_url', 'created_at', 'likes_count', 'dislikes_count', 'comments']

    def get_likes_count(self, obj):
        return obj.interactions.filter(vote='like').count()

    def get_dislikes_count(self, obj):
        return obj.interactions.filter(vote='dislike').count()


if Profile:
    class ProfileSerializer(serializers.ModelSerializer):
        user = serializers.ReadOnlyField(source='user.email')

        class Meta:
            model = Profile
            fields = ['id', 'user', 'is_2fa_enabled']
