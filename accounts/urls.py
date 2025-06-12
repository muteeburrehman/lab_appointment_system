from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views
from .views import register_user

urlpatterns = [
    # Authentication endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # User registration and status
    path('register/', register_user, name='user_register'),
    path('check-status/<str:username>/', views.check_approval_status, name='check_approval_status'),

    # Profile endpoints
    path('profile/', views.get_user_profile, name='get_user_profile'),
    path('profile/update/', views.update_user_profile, name='update_user_profile'),

    # Admin endpoints
    path('pending-users/', views.PendingUsersView.as_view(), name='pending_users'),
    path('approve-user/<int:pk>/', views.UserApprovalView.as_view(), name='approve_user'),
]