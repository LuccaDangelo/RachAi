from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

User = get_user_model()


@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Login por e-mail (username = email). Redireciona para a lista de grupos.
    """
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""

        if not email or not password:
            messages.error(request, "Informe e-mail e senha.")
        else:
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get("next") or request.POST.get("next")
                return redirect(next_url or "rachais:group_list")
            messages.error(request, "E-mail ou senha inválidos.")

    # usa o template que você já tem: templates/registration/login.html
    return render(request, "registration/login.html")


def logout_view(request):
    logout(request)
    return redirect("accounts:login")


@require_http_methods(["GET", "POST"])
def register(request):
    """
    Cadastro simples: primeiro nome + e-mail + senha.
    Faz login automático ao finalizar.
    """
    if request.method == "POST":
        first_name = (request.POST.get("first_name") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""
        confirm = request.POST.get("confirm_password") or ""

        # validações
        if not first_name:
            messages.error(request, "Informe seu primeiro nome.")
        elif not email:
            messages.error(request, "Informe um e-mail válido.")
        elif User.objects.filter(username__iexact=email).exists() or User.objects.filter(email__iexact=email).exists():
            messages.error(request, "Já existe uma conta com esse e-mail.")
        elif not password or not confirm:
            messages.error(request, "Informe e confirme a senha.")
        elif password != confirm:
            messages.error(request, "As senhas não conferem.")
        elif len(password) < 8:
            messages.error(request, "A senha deve ter pelo menos 8 caracteres.")
        else:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
            )
            # login automático
            user = authenticate(request, username=email, password=password)
            if user:
                login(request, user)
            return redirect("rachais:group_list")

    return render(request, "accounts/signup.html")
