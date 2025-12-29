from django.db import models
from accounts.models import User

class SyncLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    operation = models.CharField(max_length=50)  # e.g., 'push', 'pull'
    status = models.CharField(max_length=20, choices=(('success', 'Success'), ('failed', 'Failed'), ('conflict', 'Conflict')))
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)