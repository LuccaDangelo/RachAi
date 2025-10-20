from django.urls import path
from . import auth_views

app_name = "accounts"

urlpatterns = [
    path("entrar/", auth_views.welcome_view, name="welcome"),
    path("login/", auth_views.login_form_view, name="login"),
    path("sair/", auth_views.logout_view, name="logout"),
    path("cadastrar/", auth_views.register, name="signup"),
]
