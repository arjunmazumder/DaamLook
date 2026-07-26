from django.urls import path, include

urlpatterns = [
    path('admin/', include('users.admin_urls')),
    path('auth/', include('users.urls')),
    path('lookup/', include('lookup.urls')),
    path('core/', include('core.urls')),
    path('user/', include('users.user_urls')),
    path('services/', include('services.urls')),
    path('vendors/', include('vendors.urls')),
    path('products/', include('products.urls')),
    path('orders/', include('orders.urls')),
]
