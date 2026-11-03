from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from config.views import (
    landing_view, login_view, admin_login_view, register_view,
    user_dashboard_view, send_money_view, transactions_list_view, transaction_detail_view,
    beneficiaries_view, alerts_view, profile_view,
    admin_dashboard_view, admin_users_view, admin_transactions_view,
    admin_investigations_view, admin_analytics_view, admin_ml_model_view, admin_audit_logs_view
)

from users.views import (
    RegisterView, LoginView, LogoutView, ProfileView,
    AdminUserListView, AdminUserToggleActiveView, AuditLogListView,
    ForgotPasswordRequestOTPView, ForgotPasswordResetView
)
from beneficiaries.views import BeneficiaryViewSet
from transactions.views import TransactionListCreateView, TransactionDetailView
from fraud_detection.views import (
    FraudPredictAPIView, FraudHistoryListView, OTPGenerateView, OTPVerifyView
)
from alerts.views import AlertListView, AlertStatusUpdateView
from investigations.views import InvestigationListCreateView
from analytics.views import (
    AdminDashboardStatsView, AdminAnalyticsView, MLModelPerformanceView
)

router = DefaultRouter()
router.register(r'beneficiaries', BeneficiaryViewSet, basename='beneficiary')

urlpatterns = [
    # HTML Template Web Page Routes
    path('', landing_view, name='page-landing'),
    path('login/', login_view, name='page-login'),
    path('admin/login/', admin_login_view, name='page-admin-login'),
    path('register/', register_view, name='page-register'),
    path('dashboard/', user_dashboard_view, name='page-dashboard'),
    path('send-money/', send_money_view, name='page-send-money'),
    path('transactions/', transactions_list_view, name='page-transactions'),
    path('transactions/<int:pk>/', transaction_detail_view, name='page-transaction-detail'),
    path('beneficiaries/', beneficiaries_view, name='page-beneficiaries'),
    path('alerts/', alerts_view, name='page-alerts'),
    path('profile/', profile_view, name='page-profile'),

    path('admin/dashboard/', admin_dashboard_view, name='page-admin-dashboard'),
    path('admin/users/', admin_users_view, name='page-admin-users'),
    path('admin/transactions/', admin_transactions_view, name='page-admin-transactions'),
    path('admin/investigations/', admin_investigations_view, name='page-admin-investigations'),
    path('admin/analytics/', admin_analytics_view, name='page-admin-analytics'),
    path('admin/ml-model/', admin_ml_model_view, name='page-admin-ml-model'),
    path('admin/audit-logs/', admin_audit_logs_view, name='page-admin-audit-logs'),

    # Django Admin Panel
    path('admin/django-admin/', admin.site.urls),

    # DRF Router endpoints
    path('api/', include(router.urls)),

    # REST APIs for Authentication
    path('api/auth/register/', RegisterView.as_view(), name='auth-register'),
    path('api/auth/login/', LoginView.as_view(), name='auth-login'),
    path('api/auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('api/auth/profile/', ProfileView.as_view(), name='auth-profile'),
    path('api/auth/forgot-password/request-otp/', ForgotPasswordRequestOTPView.as_view(), name='auth-forgot-password-request'),
    path('api/auth/forgot-password/reset/', ForgotPasswordResetView.as_view(), name='auth-forgot-password-reset'),


    # REST APIs for Transactions
    path('api/transactions/', TransactionListCreateView.as_view(), name='transaction-list-create'),
    path('api/transactions/<int:pk>/', TransactionDetailView.as_view(), name='transaction-detail'),

    # REST APIs for Fraud & OTP
    path('api/fraud/predict/', FraudPredictAPIView.as_view(), name='fraud-predict'),
    path('api/fraud/history/', FraudHistoryListView.as_view(), name='fraud-history'),
    path('api/alerts/', AlertListView.as_view(), name='alert-list'),
    path('api/alerts/<int:pk>/read/', AlertStatusUpdateView.as_view(), name='alert-update'),
    path('api/otp/generate/', OTPGenerateView.as_view(), name='otp-generate'),
    path('api/otp/verify/', OTPVerifyView.as_view(), name='otp-verify'),

    # REST APIs for Admin Operations
    path('api/admin/dashboard/', AdminDashboardStatsView.as_view(), name='admin-dashboard'),
    path('api/admin/users/', AdminUserListView.as_view(), name='admin-users'),
    path('api/admin/users/<int:pk>/toggle-active/', AdminUserToggleActiveView.as_view(), name='admin-user-toggle'),
    path('api/admin/transactions/', TransactionListCreateView.as_view(), name='admin-transactions'),
    path('api/admin/fraud/', FraudHistoryListView.as_view(), name='admin-fraud'),
    path('api/admin/analytics/', AdminAnalyticsView.as_view(), name='admin-analytics'),
    path('api/admin/model-performance/', MLModelPerformanceView.as_view(), name='admin-model-performance'),
    path('api/admin/investigations/', InvestigationListCreateView.as_view(), name='admin-investigations'),
    path('api/admin/audit-logs/', AuditLogListView.as_view(), name='admin-audit-logs'),
]
