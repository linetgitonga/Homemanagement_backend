from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, SystemSettings, Household, HouseholdMembership, UserNotificationPreferences
from .forms import CustomUserCreationForm, CustomUserChangeForm


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ('username', 'email', 'phone', 'is_verified', 'preferred_language', 'is_staff', 'is_superuser', 'created_at')
    list_filter = ('is_verified', 'preferred_language', 'is_staff')
    search_fields = ('username', 'email', 'phone')
    ordering = ('-created_at',)
    # Use default Django `UserAdmin` fieldsets by not overriding them. Mark
    # some model-generated fields read-only so the admin form doesn't try to
    # edit auto-managed timestamps.
    readonly_fields = ('last_login', 'created_at', 'updated_at')
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone', 'preferred_language', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'sms_gateway', 'created_at')
    search_fields = ('sms_gateway',)
    ordering = ('-created_at',)

@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ('name', 'currency', 'created_by', 'is_active', 'created_at')
    list_filter = ('currency', 'is_active')
    search_fields = ('name', 'created_by__username')
    ordering = ('-created_at',)

@admin.register(HouseholdMembership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'household', 'role', 'joined_at')
    list_filter = ('role',)
    search_fields = ('user__username', 'household__name')
    ordering = ('-joined_at',)


@admin.register(UserNotificationPreferences)
class UserNotificationPreferencesAdmin(admin.ModelAdmin):
    list_display = ('user', 'enable_push', 'enable_sms', 'enable_email', 
                    'notify_on_expense_created', 'notify_on_refund_requested', 'updated_at')
    list_filter = ('enable_push', 'enable_sms', 'enable_email', 
                   'notify_on_expense_created', 'notify_on_refund_requested')
    search_fields = ('user__username', 'user__email')
    ordering = ('-updated_at',)
    readonly_fields = ('created_at', 'updated_at')