from rest_framework import serializers
from .models import Category, Budget, Expense, SubExpenseItem, ExpenseAttachment, RefundRequest


class CategorySerializer(serializers.ModelSerializer):
    household_name = serializers.CharField(source='household.__str__', read_only=True)

    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ('household_name',)


class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = '__all__'


class SubExpenseItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubExpenseItem
        fields = ["id", "name", "quantity", "unit_price", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ExpenseAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseAttachment
        fields = ["id", "file", "type", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ExpenseSerializer(serializers.ModelSerializer):
    sub_items = SubExpenseItemSerializer(many=True, read_only=True)
    attachments = ExpenseAttachmentSerializer(many=True, read_only=True)
    household_name = serializers.CharField(source='household.__str__', read_only=True)
    category_name = serializers.SerializerMethodField()
    recorded_by_username = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=True)

    class Meta:
        model = Expense
        fields = [
            "id", "household", "household_name", "recorded_by", "recorded_by_username",
            "created_by_name", "category", "category_name", "amount", "date", "description", "status",
            "local_id", "client_timestamp", "server_timestamp", "is_refund_requested",
            "paid_with_personal_money", "created_at", "updated_at", "sub_items",
            "attachments", "summary"
        ]
        read_only_fields = ["id", "local_id", "server_timestamp", "created_at", "updated_at"]

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_recorded_by_username(self, obj):
        return obj.recorded_by.username if obj.recorded_by else None

    def get_created_by_name(self, obj):
        return obj.recorded_by.username if obj.recorded_by else None

    def get_summary(self, obj):
        cat = obj.category.name if obj.category else 'Uncategorized'
        user = obj.recorded_by.username if obj.recorded_by else 'Unknown'
        return f"{obj.household} — {cat}: {obj.amount} on {obj.date} by {user}"


class RefundRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefundRequest
        fields = '__all__'
