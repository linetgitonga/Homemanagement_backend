import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from softdelete.models import SoftDeleteModel
from accounts.models import Household, User

class Category(models.Model):
    name = models.CharField(max_length=50)
    icon = models.CharField(max_length=100, blank=True)  # e.g., font-awesome class
    household = models.ForeignKey(Household, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.household})"

class Budget(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    limit = models.DecimalField(max_digits=12, decimal_places=2)
    period = models.CharField(max_length=20, choices=(('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Budget: {self.category} {self.limit} / {self.period}"

class Expense(SoftDeleteModel):
    STATUS_CHOICES = (('draft', 'Draft'), ('synced', 'Synced'), ('reviewed', 'Reviewed'))
    household = models.ForeignKey(Household, on_delete=models.CASCADE)
    recorded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    local_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    client_timestamp = models.DateTimeField(null=True, blank=True)
    server_timestamp = models.DateTimeField(auto_now_add=True)
    is_refund_requested = models.BooleanField(default=False)
    paid_with_personal_money = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        cat = self.category.name if self.category else 'Uncategorized'
        return f"{self.household} — {cat}: {self.amount} on {self.date} by {self.recorded_by}"

class SubExpenseItem(models.Model):
    expense = models.ForeignKey(Expense, related_name='sub_items', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} x{self.quantity} for expense #{self.expense_id}"

class ExpenseAttachment(models.Model):
    TYPE_CHOICES = (('image', 'Image'), ('voice', 'Voice Note'))
    expense = models.ForeignKey(Expense, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(upload_to='attachments/')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Attachment ({self.type}) for expense #{self.expense_id}"

class RefundRequest(SoftDeleteModel):
    STATUS_CHOICES = (('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('need_info', 'Need Info'), ('paid', 'Paid'))
    expense = models.OneToOneField(Expense, on_delete=models.CASCADE)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_refunds')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    comment = models.TextField(blank=True)
    mpesa_transaction_id = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Refund {self.amount} for expense #{self.expense_id} ({self.status})"