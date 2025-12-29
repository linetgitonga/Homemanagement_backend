from django.test import TestCase
from .models import Notification
from accounts.models import User

class NotificationsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='pass')

    def test_notification_model(self):
        notif = Notification.objects.create(user=self.user, message='Test', type='push')
        self.assertFalse(notif.is_read)