from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from core.utils import compute_hash
from django.db import transaction
from finances.models import Expense
from .models import SyncLog

class SyncPushView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payload = request.data
        client_hash = payload.get('hash')
        operations = payload.get('operations', [])

        if compute_hash(operations) != client_hash:
            return Response({"error": "Hash mismatch"}, status=status.HTTP_400_BAD_REQUEST)

        result = {"synced": [], "rejected": [], "conflicts": []}

        with transaction.atomic():
            for op in operations:
                try:
                    if op['model'] == 'finances.expense':
                        expense = self.handle_expense(op, request.user)
                        result['synced'].append({"local_id": op['local_id'], "server_id": expense.id})
                    # Add for other models
                    SyncLog.objects.create(user=request.user, operation='push', status='success', details=op)
                except Exception as e:
                    result['rejected'].append({"local_id": op['local_id'], "error": str(e)})
                    SyncLog.objects.create(user=request.user, operation='push', status='failed', details=op)

        return Response(result)

    def handle_expense(self, op, user):
        local_id = op['local_id']
        existing = Expense.objects.filter(local_id=local_id).first()
        if existing:
            if op['client_timestamp'] > existing.client_timestamp:
                for field, value in op['data'].items():
                    setattr(existing, field, value)
                existing.save()
            else:
                raise ValueError("Conflict: Older timestamp")
            return existing
        data = op['data']
        data['recorded_by'] = user
        data['local_id'] = local_id
        data['client_timestamp'] = op['client_timestamp']
        return Expense.objects.create(**data)

class SyncPullView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Pull unsynced data for user
        expenses = Expense.objects.filter(household__memberships__user=request.user, status='synced')  # Example
        data = [{"model": "finances.expense", "data": ExpenseSerializer(exp).data} for exp in expenses]
        return Response(data)