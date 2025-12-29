from django.test import TestCase
from rest_framework.test import APIClient
from .views import SyncPushView
from accounts.models import User

class SyncTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='test', password='pass')

    def test_sync_push(self):
        self.client.force_authenticate(self.user)
        data = {'hash': 'test_hash', 'operations': []}
        response = self.client.post('/api/sync/push/', data, format='json')
        self.assertEqual(response.status_code, 200)