from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from Create_Group import views as group_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Grupos
    path('groups/', include('Create_Group.urls')),

    # Auth (views nativas)
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Home -> lista de grupos (precisa bater com LOGIN_REDIRECT_URL='group_list')
    path('', group_views.group_list, name='group_list'),
]
