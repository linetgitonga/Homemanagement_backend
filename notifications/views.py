from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .models import Notification
from .serializers import NotificationSerializer
from rest_framework.permissions import IsAuthenticated

class NotificationViewSet(ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a notification as read."""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read for the current user."""
        updated = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)
        return Response({
            'detail': f'{updated} notification(s) marked as read.'
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications."""
        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        return Response({'unread_count': count})