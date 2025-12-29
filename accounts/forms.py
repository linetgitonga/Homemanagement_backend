from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'preferred_language')


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'preferred_language', 'is_active', 'is_staff', 'is_superuser', 'groups')
