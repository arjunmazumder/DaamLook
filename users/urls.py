from django.urls import path
from .views import (
    LoginView, RefreshTokenView, LogoutView, RegisterView, SendOTPView, 
    VerifyOTPView, RoleListView, ForgotPasswordView, ResetPasswordView,
    BuyerRegisterView, BuyerRegisterVerifyView, BuyerLoginView, BuyerLoginVerifyView,
    DeleteAccountSendOTPView, DeleteAccountVerifyOTPView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('getRefreshToken/', RefreshTokenView.as_view(), name='refresh-token'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('roles/', RoleListView.as_view(), name='roles'),
    path('delete-account/', DeleteAccountSendOTPView.as_view(), name='delete-account'),
    path('delete-account/verify-otp/', DeleteAccountVerifyOTPView.as_view(), name='delete-account-verify-otp'),
    
    # Buyer Passwordless Auth
    path('buyer/register/', BuyerRegisterView.as_view(), name='buyer-register'),
    path('buyer/register-verify/', BuyerRegisterVerifyView.as_view(), name='buyer-register-verify'),
    path('buyer/login/', BuyerLoginView.as_view(), name='buyer-login'),
    path('buyer/login-verify/', BuyerLoginVerifyView.as_view(), name='buyer-login-verify'),
]
