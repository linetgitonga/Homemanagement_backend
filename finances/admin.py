from django.contrib import admin
from .models import Category, Budget, Expense, SubExpenseItem, ExpenseAttachment, RefundRequest

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'household', 'icon', 'created_at')
    list_filter = ('household',)
    search_fields = ('name',)
    ordering = ('-created_at',)

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('category', 'limit', 'period', 'created_at')
    list_filter = ('period', 'category__household')
    search_fields = ('category__name',)
    ordering = ('-created_at',)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('id', 'summary_display', 'household', 'recorded_by', 'category', 'amount', 'date', 'status', 'created_at')
    list_filter = ('status', 'category', 'date', 'household')
    search_fields = ('description', 'recorded_by__username', 'category__name')
    ordering = ('-date',)
    readonly_fields = ('local_id', 'server_timestamp')
    def summary_display(self, obj):
        return str(obj)
    summary_display.short_description = 'Summary'

@admin.register(SubExpenseItem)
class SubExpenseItemAdmin(admin.ModelAdmin):
    list_display = ('expense', 'name', 'quantity', 'unit_price', 'created_at')
    list_filter = ('expense__household',)
    search_fields = ('name',)
    ordering = ('-created_at',)

@admin.register(ExpenseAttachment)
class ExpenseAttachmentAdmin(admin.ModelAdmin):
    list_display = ('expense', 'type', 'file', 'created_at')
    list_filter = ('type', 'expense__household')
    search_fields = ('file',)
    ordering = ('-created_at',)

@admin.register(RefundRequest)
class RefundRequestAdmin(admin.ModelAdmin):
    list_display = ('expense', 'requested_by', 'amount', 'status', 'reviewed_at')
    list_filter = ('status', 'expense__household')
    search_fields = ('reason', 'comment')
    ordering = ('-reviewed_at',)