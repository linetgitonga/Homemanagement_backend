from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User, Household
from .models import Expense, Category

class FinancesTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='test', password='pass')
        self.household = Household.objects.create(name='Test', created_by=self.user)
        self.category = Category.objects.create(name='Food', household=self.household)

    def test_expense_model(self):
        expense = Expense.objects.create(household=self.household, recorded_by=self.user, category=self.category, amount=100.00, date='2025-12-10')
        self.assertEqual(expense.amount, 100.00)

    def test_api_create_expense(self):
        self.client.force_authenticate(self.user)
        data = {'household': self.household.id, 'recorded_by': self.user.id, 'category': self.category.id, 'amount': 100, 'date': '2025-12-10'}
        response = self.client.post('/api/expenses/', data)
        self.assertEqual(response.status_code, 201)