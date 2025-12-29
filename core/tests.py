from django.test import TestCase
from .permissions import IsAdmin
from django.contrib.auth import get_user_model

User = get_user_model()

class PermissionsTest(TestCase):
    def test_is_admin(self):
        user = User.objects.create_user(username='test', password='pass')
        self.assertFalse(IsAdmin().has_permission(request=None, view=None))  # Mock request
        user.is_staff = True
        user.save()
        self.assertTrue(IsAdmin().has_permission(request=None, view=None))