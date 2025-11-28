"""
URL routing for user authentication APIs.
"""
from django.urls import path
from users import views

app_name = 'users'

urlpatterns = [
    # Authentication endpoints
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('refresh-token/', views.refresh_token, name='refresh-token'),
    
    # Profile endpoints (require authentication)
    path('profile/', views.get_profile, name='get-profile'),
    path('profile/update/', views.update_profile, name='update-profile'),
    
    # Password management endpoints
    path('change-password/', views.change_password, name='change-password'),
    path('forgot-password/', views.forgot_password, name='forgot-password'),
    path('reset-password/', views.reset_password, name='reset-password'),
    
    # Email verification
    path('verify-email/', views.verify_email, name='verify-email'),
    path('admin/verify-email/', views.admin_verify_email, name='admin-verify-email'),
]

