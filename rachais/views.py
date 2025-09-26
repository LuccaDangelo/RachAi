from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import Group, Participant, Expense

User = get_user_model()


def _display_name(user: User) -> str:
    """
    Nome para exibir vindo do CADASTRO (e perfis comuns):
    1) get_full_name() (first_name + last_name)
    2) first_name
    3) user.name / user.full_name / user.display_name
    4) user.profile.(display_name|name|full_name) se existir
    5) username sem domínio (se for e-mail)
    """
    if not user:
        return "Usuário"

    # 1 e 2: campos padrão do Django
    full = (user.get_full_name() or "").strip()
    if full:
        return full
    first = (getattr(user, "first_name", "") or "").strip()
    if first:
        return first

    # 3: campos comuns em modelos customizados
    for attr in ("name", "full_name", "display_name"):
        val = (getattr(user, attr, "") or "").strip()
        if val:
            return val

    # 4: perfil relacionado (OneToOne 'profile' muito comum)
    prof = getattr(user, "profile", None)
    if prof:
        for attr in ("display_name", "name", "full_name", "first_name"):
            val = (getattr(prof, attr, "") or "").strip()
            if val:
                return val

    # 5: fallback — username sem domínio se parecer e-mail
    uname = (getattr(user, "username", "") or "").strip()
    if "@" in uname:
        uname = uname.split("@", 1)[0]
    return uname or "Usuário"


@login_required
def group_list(request):
    """Lista apenas os grupos em que o usuário é participante (ou criou)."""
    groups = (
        Group.objects
        .filter(Q(participants__user=request.user) | Q(creator=request.user))
        .distinct()
        .order_by("-created_at")
        .prefetch_related("participants__user")
    )
    return render(request, "rachais/group_list.html", {"groups": groups})


@login_required
def group_detail(request, group_id):
    """Exibe um grupo somente se o usuário for participante ou criador."""
    group = get_object_or_404(
        Group.objects.filter(
            Q(participants__user=request.user) | Q(creator=request.user)
        ).distinct(),
        pk=group_id,
    )

    expenses = list(group.expenses.select_related("paid_by").all())
    participants = list(group.participants.select_related("user").all())

    # Nome amigável para cada participante
    for p in participants:
        setattr(p, "display_name", _display_name(p.user))

    total = sum((e.amount for e in expenses), Decimal("0"))

    # Divisão igual por despesa
    users_in_group = [p.user for p in participants]
    n_participants = len(users_in_group)

    for e in expenses:
        setattr(e, "paid_by_name", _display_name(e.paid_by))

        split_list = []
        if n_participants > 0:
            cota = (e.amount / Decimal(n_participants)).quantize(Decimal("0.01"))
            for u in users_in_group:
                if u.id == e.paid_by_id:
                    continue  # quem pagou não deve a si mesmo
                split_list.append({
                    "name": _display_name(u),
                    "amount": cota,
                })
        setattr(e, "split_list", split_list)

    return render(
        request,
        "rachais/group_detail.html",
        {
            "group": group,
            "expenses": expenses,
            "participants": participants,
            "total": total,
        },
    )


@login_required
def create_group(request):
    """Cria um grupo e adiciona automaticamente o criador como participante."""
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()

        if not name:
            messages.error(request, "Informe um nome para o grupo.")
        elif len(name) > 100:
            messages.error(request, "O nome deve ter no máximo 100 caracteres.")
        elif Group.objects.filter(name__iexact=name).exists():
            messages.error(request, "Já existe um grupo com esse nome.")
        else:
            new_group = Group.objects.create(name=name, creator=request.user)
            Participant.objects.get_or_create(group=new_group, user=request.user)
            messages.success(request, "Grupo criado com sucesso!")
            return redirect("rachais:group_detail", group_id=new_group.id)

    return render(request, "rachais/create_group.html")


@login_required
def add_participant(request, group_id):
    """
    Adiciona participante por username OU e-mail.
    Somente o criador do grupo pode adicionar.
    """
    group = get_object_or_404(Group, pk=group_id)

    if request.user != group.creator:
        messages.error(request, "Apenas o criador do grupo pode adicionar participantes.")
        return redirect("rachais:group_detail", group_id=group.id)

    if request.method == "POST":
        ident = (request.POST.get("identifier") or "").strip()  # username OU e-mail

        if not ident:
            messages.error(request, "Informe o username ou e-mail do usuário.")
            return redirect("rachais:group_detail", group_id=group.id)

        # procura primeiro por username; se não achar, tenta por e-mail
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
        messages.success(request, f"{_display_name(user)} adicionado(a) com sucesso!")
        return redirect("rachais:group_detail", group_id=group.id)

    return redirect("rachais:group_detail", group_id=group.id)


@login_required
def add_expense(request, group_id):
    """
    Adiciona uma despesa ao grupo (apenas participantes podem registrar).
    Valida valor > 0 e que o pagador pertença ao grupo.
    """
    group = get_object_or_404(Group, pk=group_id)

    if not Participant.objects.filter(group=group, user=request.user).exists():
        messages.error(request, "Você não participa deste grupo.")
        return redirect("rachais:group_detail", group_id=group.id)

    participants = list(group.participants.select_related("user").all())
    for p in participants:
        setattr(p, "display_name", _display_name(p.user))

    if request.method == "POST":
        description = (request.POST.get("description") or "").strip()
        raw_amount = (request.POST.get("amount") or "").strip()
        paid_by_id = request.POST.get("paid_by")

        if not description:
            messages.error(request, "Informe a descrição da despesa.")
            return render(request, "rachais/add_expense.html", {"group": group, "participants": participants})

        # aceita "100", "100,00", "1.234,56"
        norm = raw_amount.replace(".", "").replace(",", ".")
        try:
            amount = Decimal(norm)
        except (InvalidOperation, AttributeError):
            messages.error(request, "Informe um valor válido (ex.: 100,00).")
            return render(request, "rachais/add_expense.html", {"group": group, "participants": participants})

        if amount <= 0:
            messages.error(request, "O valor da despesa deve ser maior que zero")
            return render(request, "rachais/add_expense.html", {"group": group, "participants": participants})

        try:
            payer = User.objects.get(pk=paid_by_id)
        except (User.DoesNotExist, ValueError, TypeError):
            messages.error(request, "Selecione quem pagou.")
            return render(request, "rachais/add_expense.html", {"group": group, "participants": participants})

        if not Participant.objects.filter(group=group, user=payer).exists():
            messages.error(request, "O pagador precisa ser participante do grupo.")
            return render(request, "rachais/add_expense.html", {"group": group, "participants": participants})

        Expense.objects.create(group=group, description=description, amount=amount, paid_by=payer)
        messages.success(request, "Despesa registrada com sucesso.")
        return redirect("rachais:group_detail", group_id=group.id)

    return render(request, "rachais/add_expense.html", {"group": group, "participants": participants})
