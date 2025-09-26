# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout  # <- adiciona authenticate (e logout se já usa logout_view)

def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            raw_password = form.cleaned_data["password1"]

            # Autentica para o Django saber qual backend usar
            user_auth = authenticate(request, username=user.username, password=raw_password)
            if user_auth is not None:
                login(request, user_auth)
                return redirect("rachais:group_list")

            # Fallback: se por algum motivo não autenticou agora
            return redirect("accounts:login")
    else:
        form = UserCreationForm()

    return render(request, "accounts/signup.html", {"form": form})

# (opcional) se já estiver usando logout por GET:
def logout_view(request):
    logout(request)
    return redirect("accounts:login")
