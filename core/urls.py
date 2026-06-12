from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('payments/', include('payments.urls')),
    path('api/accounts/', include('accounts.urls')),
    path('api/chamas/', include('chamas.urls')),
    path('api/contributions/', include('contributions.urls')),
    path('api/loans/', include('loans.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('', include('core_pages.urls')),
    path('api/chat/', include('chat.urls')),
]