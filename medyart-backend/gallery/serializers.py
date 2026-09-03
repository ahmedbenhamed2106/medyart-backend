from rest_framework import serializers
from gallery.models import PhotoModel

class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhotoModel
        fields = ['id', 'title', 'image_url', 'created_at']
