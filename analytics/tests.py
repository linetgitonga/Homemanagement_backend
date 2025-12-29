from django.test import TestCase
from rest_framework.test import APIClient
from .views import ReportViewSet

class AnalyticsTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_report_generation(self):
        # Add test data
        response = self.client.get('/api/reports/?period=daily&format=json')
        self.assertEqual(response.status_code, 200)  # Assuming auth in setup