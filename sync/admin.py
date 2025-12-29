from django.contrib import admin
from .models import SyncLog

@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'operation', 'status', 'created_at')
    list_filter = ('operation', 'status')
    search_fields = ('details', 'user__username')
    ordering = ('-created_at',)