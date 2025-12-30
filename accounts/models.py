from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields
from softdelete.models import SoftDeleteModel

class User(AbstractUser):
    phone = models.CharField(max_length=15, unique=True, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    preferred_language = models.CharField(max_length=10, default='en')
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username


class UserNotificationPreferences(models.Model):
    """User preferences for different types of notifications."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Notification channels
    enable_push = models.BooleanField(default=True)
    enable_sms = models.BooleanField(default=False)
    enable_email = models.BooleanField(default=True)
    
    # Event types
    notify_on_expense_created = models.BooleanField(default=True)
    notify_on_refund_requested = models.BooleanField(default=True)
    notify_on_refund_approved = models.BooleanField(default=True)
    notify_on_refund_rejected = models.BooleanField(default=True)
    notify_on_budget_exceeded = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Notification preferences for {self.user.username}"

class SystemSettings(models.Model):
    languages = models.JSONField(default=list)  # e.g., ['en', 'sw']
    sms_gateway = models.CharField(max_length=100, blank=True)
    supported_currencies = models.JSONField(default=list)  # e.g., ['KES', 'USD']
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Household(TranslatableModel, SoftDeleteModel):
    
    translations = TranslatedFields(
        name=models.CharField(max_length=100),
    )
    currency = models.CharField(max_length=3, default="KES")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # Parler provides `safe_translation_getter` to fetch translated fields
        name = self.safe_translation_getter('name', any_language=True)
        return name or f"Household {self.pk}"

class HouseholdMembership(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),  # System admin, but per household? No, admin is global
        ('homeowner', 'Homeowner'),
        ('helper', 'Helper'),
        ('viewer', 'Viewer'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    joined_at = models.DateTimeField(auto_now_add=True)
    invited_by = models.ForeignKey(User, related_name='invited_members', null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'household')