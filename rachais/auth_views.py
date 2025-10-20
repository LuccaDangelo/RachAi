from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

User = get_user_model()


def welcome_view(request):
    return render(request, "rachais/index.html")


@require_http_methods(["GET", "POST"])
def login_form_view(request):
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = (request.POST.get("password") or "")

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            next_url = request.GET.get("next")
            return redirect(next_url or "rachais:home")
        
        messages.error(request, "E-mail ou senha inválidos.")

    return render(request, "rachais/login.html")


def logout_view(request):
    logout(request)
    return redirect("accounts:welcome")


@require_http_methods(["GET", "POST"])
def register(request):
    if request.method == "POST":
        first_name = (request.POST.get("first_name") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()
        password = (request.POST.get("password") or "")
        confirm = (request.POST.get("confirm_password") or "")

        if not first_name:
            messages.error(request, "Informe seu primeiro nome.")
        elif not email:
            messages.error(request, "Informe um e-mail válido.")
        elif User.objects.filter(username__iexact=email).exists():
            messages.error(request, "Já existe uma conta com esse e-mail.")
        elif not password or not confirm:
            messages.error(request, "Informe e confirme a senha.")
        elif password != confirm:
            messages.error(request, "As senhas não conferem.")
        elif len(password) < 8:
            messages.error(request, "A senha deve ter pelo menos 8 caracteres.")
        else:
            User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
            )
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect("rachais:home")
    return render(request, "rachais/signup.html")