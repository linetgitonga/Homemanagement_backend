from rest_framework import serializers
from .models import User, SystemSettings, Household, HouseholdMembership, UserNotificationPreferences

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'phone', 'preferred_language')


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change endpoint."""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        """Validate that the old password is correct."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate(self, data):
        """Validate that new passwords match."""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                "confirm_password": "New password and confirm password do not match."
            })
        
        # Validate password strength
        if len(data['new_password']) < 8:
            raise serializers.ValidationError({
                "new_password": "Password must be at least 8 characters long."
            })
        
        return data

    def save(self, **kwargs):
        """Set the new password."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserNotificationPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotificationPreferences
        fields = '__all__'
        read_only_fields = ('user',)

class SystemSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSettings
        fields = '__all__'

class HouseholdSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Household
        fields = '__all__'
        read_only_fields = ('name',)

    def get_name(self, obj):
        try:
            return obj.safe_translation_getter('name', any_language=True) or str(obj)
        except Exception:
            return str(obj)

class HouseholdMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    invited_by = UserSerializer(read_only=True, allow_null=True)
    household_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = HouseholdMembership
        fields = ('id', 'household', 'household_name', 'user', 'role', 'joined_at', 'invited_by', 'created_at', 'updated_at')

    def get_household_name(self, obj):
        try:
            return obj.household.safe_translation_getter('name', any_language=True) or str(obj.household)
        except Exception:
            return str(obj.household)


from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email_or_phone'
    def validate(self, attrs):
        email_or_phone = attrs.get(self.username_field) or attrs.get('email_or_phone')
        password = attrs.get('password')

        if not email_or_phone or not password:
            raise serializers.ValidationError('Must include email_or_phone and password')

        # Try to find user by email or phone
        user = None
        if '@' in email_or_phone:
            user = User.objects.filter(email__iexact=email_or_phone).first()
        else:
            user = User.objects.filter(phone=email_or_phone).first()

        if not user or not user.check_password(password) or not user.is_active:
            raise serializers.ValidationError('No active account found with the given credentials')

        refresh = self.get_token(user)

        # Build user payload for frontend
        user_data = UserSerializer(user).data

        # Gather household membership roles
        try:
            from .models import HouseholdMembership
            memberships = HouseholdMembership.objects.filter(user=user).select_related('household')
            roles = []
            for m in memberships:
                try:
                    hname = m.household.safe_translation_getter('name', any_language=True) or str(m.household)
                except Exception:
                    hname = str(m.household_id)
                roles.append({'household_id': m.household_id, 'household_name': hname, 'role': m.role})
        except Exception:
            roles = []

        # Determine a simple user_type for frontend routing
        if user.is_superuser:
            user_type = 'system_admin'
        elif user.is_staff:
            user_type = 'staff'
        else:
            # prefer homeowner > helper > viewer
            priority = {'homeowner': 3, 'helper': 2, 'viewer': 1}
            best = None
            best_score = 0
            for r in roles:
                score = priority.get(r.get('role'), 0)
                if score > best_score:
                    best_score = score
                    best = r.get('role')
            user_type = best or 'user'

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': user_data,
            'roles': roles,
            'user_type': user_type,
        }