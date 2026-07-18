from django.urls import path
# pyrefly: ignore [missing-import]
from .views import UpdateLocationView, UpdateCustomerLocationView

urlpatterns = [
    path('update-location/', UpdateLocationView.as_view(), name='update-location'),
    path('update-customer-location/', UpdateCustomerLocationView.as_view(), name='update-customer-location'),
]
