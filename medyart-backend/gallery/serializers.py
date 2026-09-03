from rest_framework import viewsets
from gallery.models import PhotoModel
from gallery.serializers import PhotoSerializer

class PhotoViewSet(viewsets.ModelViewSet):
    queryset = PhotoModel.objects.all().order_by('-created_at')
    serializer_class = PhotoSerializer
