from rest_framework import serializers
from django.contrib.auth.models import User
from gallery.models import PhotoModel, InteractionModel, CommentModel

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
