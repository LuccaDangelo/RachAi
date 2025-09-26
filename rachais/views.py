from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Group, Participant

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
            return redirect("rachais:group_detail", group_id=new_group.id)

    # GET ou POST inválido → renderiza o form simples
    return render(request, "rachais/create_group.html")
