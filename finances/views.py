from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from django.utils import timezone
from core.permissions import IsHomeowner,IsAdmin, IsHelperInHousehold, IsOwnerOrAdmin, IsViewerInHousehold
from .models import Category, Budget, Expense, RefundRequest, SubExpenseItem, ExpenseAttachment
from .serializers import CategorySerializer, BudgetSerializer, ExpenseSerializer, RefundRequestSerializer, SubExpenseItemSerializer, ExpenseAttachmentSerializer
from notifications.utils import notify_expense_created, notify_refund_requested, notify_refund_status_changed

class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsHelperInHousehold | IsHomeowner | IsAdmin]

    def get_queryset(self):
        return Category.objects.filter(household=self.request.user.householdmembership_set.first().household)

class BudgetViewSet(ModelViewSet):
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated, IsHomeowner | IsAdmin]

    def get_queryset(self):
        return Budget.objects.filter(category__household=self.request.user.householdmembership_set.first().household)

class ExpenseViewSet(ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Expense.objects.all()
        return Expense.objects.filter(household__memberships__user=user)

    def get_permissions(self):
        if self.action == 'list':
            self.permission_classes += [IsViewerInHousehold]
        elif self.action in ['create', 'update']:
            self.permission_classes += [IsHelperInHousehold | IsHomeowner]
        elif self.action == 'destroy':
            self.permission_classes += [IsOwnerOrAdmin]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Override to send notifications when expense is created."""
        expense = serializer.save()
        # Send notifications to household members
        try:
            notify_expense_created(expense)
        except Exception as e:
            # Log error but don't fail the expense creation
            print(f"Failed to send notification: {e}")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        household_q = request.query_params.get("household")
        if household_q:
            try:
                if int(household_q) != instance.household_id:
                    return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
            except ValueError:
                return Response({"detail": "Invalid household id."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class SubExpenseItemViewSet(ModelViewSet):
    """API endpoint for creating and managing sub-expense items."""
    queryset = SubExpenseItem.objects.all()
    serializer_class = SubExpenseItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return SubExpenseItem.objects.all()
        return SubExpenseItem.objects.filter(expense__household__memberships__user=user)

    def get_permissions(self):
        if self.action == 'list':
            self.permission_classes += [IsViewerInHousehold]
        elif self.action in ['create', 'update', 'partial_update']:
            self.permission_classes += [IsHelperInHousehold | IsHomeowner]
        elif self.action == 'destroy':
            self.permission_classes += [IsOwnerOrAdmin]
        return super().get_permissions()

class RefundRequestViewSet(ModelViewSet):
    queryset = RefundRequest.objects.all()
    serializer_class = RefundRequestSerializer
    permission_classes = [IsAuthenticated, IsHelperInHousehold | IsHomeowner]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return RefundRequest.objects.all()
        if 'homeowner' in user.householdmembership_set.first().role:
            return RefundRequest.objects.filter(expense__household__memberships__user=user)
        return RefundRequest.objects.filter(requested_by=user)

    def perform_create(self, serializer):
        """Override to send notifications when refund is requested."""
        refund_request = serializer.save()
        # Send notifications to homeowners
        try:
            notify_refund_requested(refund_request)
        except Exception as e:
            # Log error but don't fail the refund creation
            print(f"Failed to send notification: {e}")

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsHomeowner | IsAdmin])
    def approve(self, request, pk=None):
        """Approve a refund request."""
        refund_request = self.get_object()
        
        if refund_request.status != 'pending':
            return Response(
                {"detail": f"Cannot approve refund with status '{refund_request.status}'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        refund_request.status = 'approved'
        refund_request.reviewed_by = request.user
        refund_request.reviewed_at = timezone.now()
        refund_request.comment = request.data.get('comment', '')
        refund_request.save()
        
        # Send notification to requester
        try:
            notify_refund_status_changed(refund_request, 'approved')
        except Exception as e:
            print(f"Failed to send notification: {e}")
        
        serializer = self.get_serializer(refund_request)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsHomeowner | IsAdmin])
    def reject(self, request, pk=None):
        """Reject a refund request."""
        refund_request = self.get_object()
        
        if refund_request.status != 'pending':
            return Response(
                {"detail": f"Cannot reject refund with status '{refund_request.status}'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        refund_request.status = 'rejected'
        refund_request.reviewed_by = request.user
        refund_request.reviewed_at = timezone.now()
        refund_request.comment = request.data.get('comment', '')
        refund_request.save()
        
        # Send notification to requester
        try:
            notify_refund_status_changed(refund_request, 'rejected')
        except Exception as e:
            print(f"Failed to send notification: {e}")
        
        serializer = self.get_serializer(refund_request)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsHomeowner | IsAdmin])
    def mark_paid(self, request, pk=None):
        """Mark a refund request as paid."""
        refund_request = self.get_object()
        
        if refund_request.status != 'approved':
            return Response(
                {"detail": "Only approved refunds can be marked as paid."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        mpesa_transaction_id = request.data.get('mpesa_transaction_id', '')
        if not mpesa_transaction_id:
            return Response(
                {"detail": "M-Pesa transaction ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        refund_request.status = 'paid'
        refund_request.mpesa_transaction_id = mpesa_transaction_id
        refund_request.save()
        
        # Send notification to requester
        try:
            notify_refund_status_changed(refund_request, 'paid')
        except Exception as e:
            print(f"Failed to send notification: {e}")
        
        serializer = self.get_serializer(refund_request)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsHomeowner | IsAdmin])
    def request_info(self, request, pk=None):
        """Request additional information for a refund request."""
        refund_request = self.get_object()
        
        if refund_request.status not in ['pending', 'need_info']:
            return Response(
                {"detail": "Cannot request info for refunds that are approved, rejected, or paid."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        refund_request.status = 'need_info'
        refund_request.reviewed_by = request.user
        refund_request.reviewed_at = timezone.now()
        refund_request.comment = request.data.get('comment', '')
        refund_request.save()
        
        # Send notification to requester
        try:
            notify_refund_status_changed(refund_request, 'need_info')
        except Exception as e:
            print(f"Failed to send notification: {e}")
        
        serializer = self.get_serializer(refund_request)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ExpenseAttachmentViewSet(ModelViewSet):
    queryset = ExpenseAttachment.objects.all()
    serializer_class = ExpenseAttachmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return ExpenseAttachment.objects.all()
        return ExpenseAttachment.objects.filter(expense__household__memberships__user=user)