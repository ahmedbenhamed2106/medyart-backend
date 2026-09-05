from django.db import models
from django.contrib.auth.models import User

# Profile model for 2FA settings
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    two_factor_secret = models.CharField(max_length=64, blank=True, null=True)
    is_2fa_enabled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class PhotoModel(models.Model):
    title = models.CharField(max_length=255)
    image_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class InteractionModel(models.Model):
    LIKE = 'like'
    DISLIKE = 'dislike'
    VOTE_CHOICES = [(LIKE, 'Like'), (DISLIKE, 'Dislike')]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    photo = models.ForeignKey(PhotoModel, on_delete=models.CASCADE, related_name='interactions')
    vote = models.CharField(max_length=10, choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'photo')

class CommentModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    photo = models.ForeignKey(PhotoModel, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.photo.title}"

class OrderModel(models.Model):
    TIER_PRICES = [
        ('HD', 3.00),
        ('1080P', 5.00),
        ('1440P', 7.00),
        ('4K', 9.00),
        ('8K', 12.00),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    photo = models.ForeignKey(PhotoModel, on_delete=models.CASCADE)
    resolution = models.CharField(max_length=10)
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    stripe_intent_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.user.username} - {self.resolution}"
