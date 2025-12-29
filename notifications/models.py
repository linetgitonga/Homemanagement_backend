from django.db import models
from accounts.models import User

class Notification(models.Model):
    TYPE_CHOICES = (('push', 'Push'), ('sms', 'SMS'), ('email', 'Email'))
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)