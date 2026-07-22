from django.urls import path, include

urlpatterns = [
    path('auth/', include('users.urls')),
    path('lookup/', include('lookup.urls')),
    path('core/', include('core.urls')),
    path('user/', include('users.user_urls')),
    path('services/', include('services.urls')),
    path('vendors/', include('vendors.urls')),
    path('products/', include('products.urls')),
]
