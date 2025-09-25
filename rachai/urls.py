

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('rachais.urls', namespace='rachais')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
]
