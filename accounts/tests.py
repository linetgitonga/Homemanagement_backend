from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from .models import User, Household

class AccountsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='test', password='pass')

    def test_user_model(self):
        self.assertEqual(self.user.username, 'test')

    def test_household_creation(self):
        household = Household.objects.create(name='Test House', created_by=self.user, currency='KES')
        self.assertEqual(household.name, 'Test House')

    def test_api_list_users(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, 403)  # Since not admin