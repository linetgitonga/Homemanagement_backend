from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from core.permissions import IsAdmin, IsHomeowner
from .models import User, Household, UserNotificationPreferences, HouseholdMembership
from .serializers import (
    UserSerializer, HouseholdSerializer, UserNotificationPreferencesSerializer, 
    HouseholdMembershipSerializer, ChangePasswordSerializer
)
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import serializers
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'phone', 'password', 'confirm_password', 'first_name', 'last_name')

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')
        user = User.objects.create_user(**validated_data)
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        return user

class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"detail": "Registration successful."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]  # Admins only for user management

    @action(detail=False, methods=['get', 'put', 'patch'])
    def notification_preferences(self, request):
        """Get or update the current user's notification preferences."""
        user = request.user
        
        # Get or create preferences
        preferences, created = UserNotificationPreferences.objects.get_or_create(user=user)
        
        if request.method == 'GET':
            serializer = UserNotificationPreferencesSerializer(preferences)
            return Response(serializer.data)
        
        elif request.method in ['PUT', 'PATCH']:
            partial = request.method == 'PATCH'
            serializer = UserNotificationPreferencesSerializer(
                preferences, 
                data=request.data, 
                partial=partial
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """Change the current user's password."""
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'detail': 'Password changed successfully.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class HouseholdViewSet(ModelViewSet):
    queryset = Household.objects.all()
    serializer_class = HouseholdSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Household.objects.all()
        return Household.objects.filter(memberships__user=self.request.user)

    def get_permissions(self):
        if self.action in ['create', 'update', 'destroy']:
            self.permission_classes = [IsAdmin | IsHomeowner]
        return super().get_permissions()

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """Get all members of a household."""
        household = self.get_object()
        memberships = HouseholdMembership.objects.filter(household=household).select_related('user', 'invited_by')
        serializer = HouseholdMembershipSerializer(memberships, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsHomeowner | IsAdmin])
    def add_member(self, request, pk=None):
        """Add a member to the household."""
        household = self.get_object()
        user_id = request.data.get('user_id')
        role = request.data.get('role', 'viewer')

        if not user_id:
            return Response(
                {'detail': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'detail': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if membership already exists
        if HouseholdMembership.objects.filter(household=household, user=user).exists():
            return Response(
                {'detail': 'User is already a member of this household'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        membership = HouseholdMembership.objects.create(
            household=household,
            user=user,
            role=role,
            invited_by=request.user
        )

        serializer = HouseholdMembershipSerializer(membership)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated, IsHomeowner | IsAdmin])
    def remove_member(self, request, pk=None):
        """Remove a member from the household."""
        household = self.get_object()
        user_id = request.data.get('user_id')

        if not user_id:
            return Response(
                {'detail': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            membership = HouseholdMembership.objects.get(household=household, user_id=user_id)
            membership.delete()
            return Response(
                {'detail': 'Member removed successfully'}, 
                status=status.HTTP_200_OK
            )
        except HouseholdMembership.DoesNotExist:
            return Response(
                {'detail': 'Member not found in this household'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"detail": "If the email exists, a reset link will be sent."}, status=status.HTTP_200_OK)
            # Generate token and uid
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"http://localhost:3000/password-reset-confirm/{uid}/{token}/"
            # For dev: print to console
            print(f"Password reset link for {email}: {reset_link}")
            # In production, send email:
            # send_mail('Password Reset', f'Use this link: {reset_link}', 'no-reply@ledger.com', [email])
            return Response({"detail": "If the email exists, a reset link will be sent."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)