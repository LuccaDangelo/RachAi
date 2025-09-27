from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(("rachais.urls", "rachais"), namespace='rachais')),
    path('accounts/', include(('rachais.auth_urls', 'accounts'), namespace='accounts')),
]
