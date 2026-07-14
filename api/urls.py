from django.urls import path, include

urlpatterns = [
    path('auth/', include('users.urls')),
    path('lookup/', include('lookup.urls')),
    path('user/', include('users.user_urls')),
]
