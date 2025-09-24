from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .forms import SignUpForm

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Cadastro realizado. Bem-vindo!')
            return redirect('rachais:group_list') 
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})
