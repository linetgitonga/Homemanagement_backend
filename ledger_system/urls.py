from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView
from accounts.auth import CustomTokenObtainPairView

from accounts.views import UserViewSet, HouseholdViewSet
from finances.views import ExpenseViewSet, RefundRequestViewSet,ExpenseAttachmentViewSet, CategoryViewSet, BudgetViewSet, SubExpenseItemViewSet
from analytics.views import ReportViewSet
from notifications.views import NotificationViewSet
from sync.views import SyncPushView, SyncPullView
from accounts.serializers import CustomTokenObtainPairSerializer

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'households', HouseholdViewSet)
router.register(r'expenses', ExpenseViewSet)
router.register(r'refunds', RefundRequestViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'budgets', BudgetViewSet)
router.register(r'subexpenses', SubExpenseItemViewSet)
router.register(r'expense-attachments', ExpenseAttachmentViewSet)
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'notifications', NotificationViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/sync/push/', SyncPushView.as_view(), name='sync-push'),
    path('api/sync/pull/', SyncPullView.as_view(), name='sync-pull'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # JWT auth endpoints (explicit) - SimpleJWT does not provide a urls module
    path('api/auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)