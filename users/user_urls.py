from django.urls import path
from .views import KYCProfileView

urlpatterns = [
    path('profile/', KYCProfileView.as_view(), name='user-profile'),
]
