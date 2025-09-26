from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model  # <- novo
from .models import Group, Participant

User = get_user_model()  # <- novo

def group_list(request):
    groups = Group.objects.all().order_by("-created_at")
    return render(request, "rachais/group_list.html", {"groups": groups})

def group_detail(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    return render(request, "rachais/group_detail.html", {"group": group})

@login_required
def create_group(request):
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()

        # validações manuais (sem Django forms)
        if not name:
            messages.error(request, "Informe um nome para o grupo.")
        elif len(name) > 100:
            messages.error(request, "O nome deve ter no máximo 100 caracteres.")
        elif Group.objects.filter(name__iexact=name).exists():
            messages.error(request, "Já existe um grupo com esse nome.")
        else:
            new_group = Group.objects.create(name=name, creator=request.user)
            Participant.objects.get_or_create(group=new_group, user=request.user)
            messages.success(request, "Grupo criado com sucesso!")  # banner verde
            return redirect("rachais:group_detail", group_id=new_group.id)

    # GET ou POST inválido → renderiza o form simples
    return render(request, "rachais/create_group.html")

@login_required
def add_participant(request, group_id):
    group = get_object_or_404(Group, pk=group_id)

    # opcional: apenas o criador pode adicionar
    if request.user != group.creator:
        messages.error(request, "Apenas o criador do grupo pode adicionar participantes.")
        return redirect("rachais:group_detail", group_id=group.id)

    if request.method == "POST":
        ident = (request.POST.get("identifier") or "").strip()  # username OU e-mail

        if not ident:
            messages.error(request, "Informe o username ou e-mail do usuário.")
            return redirect("rachais:group_detail", group_id=group.id)

        # procura por username; se não achar, tenta por e-mail
        try:
            user = User.objects.get(username__iexact=ident)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email__iexact=ident)
            except User.DoesNotExist:
                user = None

        if not user:
            messages.error(request, "Usuário não encontrado.")
            return redirect("rachais:group_detail", group_id=group.id)

        if Participant.objects.filter(group=group, user=user).exists():
            messages.info(request, "Esse usuário já está no grupo.")
            return redirect("rachais:group_detail", group_id=group.id)

        Participant.objects.create(group=group, user=user)
        messages.success(request, f"{user.username} adicionado com sucesso!")
        return redirect("rachais:group_detail", group_id=group.id)

    return redirect("rachais:group_detail", group_id=group.id)
