from django.urls import path
from django.contrib.auth import views as auth_views
from .views import signup, logout_view  # <-- importa

app_name = "accounts"

urlpatterns = [
    path("signup/", signup, name="signup"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            redirect_authenticated_user=False,
        ),
        name="login",
    ),
    path("logout/", logout_view, name="logout"),  # <-- usa a view própria (GET)
]
