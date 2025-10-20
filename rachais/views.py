from decimal import Decimal, InvalidOperation
import decimal
from typing import Optional
from collections import defaultdict
from types import SimpleNamespace

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db.models import Q

from .models import Group, Participant, Expense

User = get_user_model()


def _display_name(user: Optional[AbstractUser]) -> str:
    if not user:
        return "Usuário"

    full = (user.get_full_name() or "").strip()
    if full:
        return full

    first = (getattr(user, "first_name", "") or "").strip()
    if first:
        return first

    for attr in ("name", "full_name", "display_name"):
        val = (getattr(user, attr, "") or "").strip()
        if val:
            return val

    prof = getattr(user, "profile", None)
    if prof:
        for attr in ("display_name", "name", "full_name", "first_name"):
            val = (getattr(prof, attr, "") or "").strip()
            if val:
                return val

    uname = (getattr(user, "username", "") or "").strip()
    if "@" in uname:
        uname = uname.split("@", 1)[0]
    return uname or "Usuário"


def _sidebar_groups_qs(user: User):
    """QS padrão para preencher a sidebar com os grupos do usuário."""
    return (
        Group.objects
        .filter(Q(participants__user=user) | Q(creator=user))
        .distinct()
        .order_by("-created_at")
        .prefetch_related("participants__user")
    )

def _calculate_balances(group):
    participants = list(group.participants.select_related("user").all())
    expenses = list(group.expenses.select_related("paid_by").all())

    if not participants:
        return{}
    
    n_participants = len(participants)
    balances = defaultdict(Decimal)

    for expense in expenses:
        if n_participants <= 0:
            continue

        share = (expense.amount / Decimal(n_participants)).quantize(Decimal("0.01"))


        balances[expense.paid_by.id] += expense.amount

        for participant in participants:
            balances[participant.user.id] -= share
    
    return dict(balances)

def _calculate_settlements(balances, participants_qs):
    user_map = {p.user.id: p.user for p in participants_qs}
    creditors = []
    debtors = []

    for user_id, balance in balances.items():
        if balance > Decimal("0.01"):
            creditors.append([user_id, balance])
        elif balance < Decimal("-0.01"):
            debtors.append([user_id, -balance])
    
    settlements = []
    i = j = 0

    while i < len(creditors) and j < len(debtors):
        creditor_id, credit = creditors[i]
        debtor_id, debt = debtors[j]
        transfer = min(credit, debt).quantize(Decimal("0.01"))

        settlements.append(SimpleNamespace(
            person_from=user_map[debtor_id],
            person_to=user_map[creditor_id],
            amount=transfer,  
        ))

        creditors[i][1] -= transfer
        debtors[j][1] -= transfer

        if creditors[i][1] < Decimal("0.01"):
            i+=1
        if debtors[j][1] < Decimal("0.01"):
            j+=1
    
    return settlements


# ---------------------- VIEWS ---------------------- #

@login_required
def group_list(request):
    groups = _sidebar_groups_qs(request.user)
    return render(request, "rachais/group_list.html", {"groups": groups})


@login_required
def group_detail(request, group_id):
    groups = _sidebar_groups_qs(request.user)  
    group = get_object_or_404(groups, pk=group_id)

    expenses = list(group.expenses.select_related("paid_by").all())
    participants = list(group.participants.select_related("user").all())

    for p in participants:
        setattr(p, "display_name", _display_name(p.user))

    total = sum((e.amount for e in expenses), Decimal("0"))
    balances = _calculate_balances(group)
    settlements = _calculate_settlements(balances, participants)

    for s in settlements:
        setattr(s, "from_name", _display_name(s.person_from))
        setattr(s, "to_name", _display_name(s.person_to))

    for participant in participants:
        balance = balances.get(participant.user.id, Decimal("0"))
        setattr(participant, "balance", balance)
        setattr(participant, "balance_abs", balance.copy_abs())
    
    users_in_group = [p.user for p in participants]
    n_participants = len(users_in_group)

    for e in expenses:
        setattr(e, "paid_by_name", _display_name(e.paid_by))
        split_list = []
        if n_participants > 0:
            cota = (e.amount / Decimal(n_participants)).quantize(Decimal("0.01"))
            for u in users_in_group:
                if u.id == e.paid_by_id:
                    continue
                split_list.append({"name": _display_name(u), "amount": cota})
        setattr(e, "split_list", split_list)

    return render(
        request,
        "rachais/group_detail.html",
        {
            "group": group,
            "groups": groups,           
            "expenses": expenses,
            "participants": participants,
            "total": total,
            "settlements": settlements,
        },
    )


@login_required
def create_group(request):
    """Cria um grupo; impede nomes repetidos apenas para o MESMO criador."""
    groups = _sidebar_groups_qs(request.user)

    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()

        if not name:
            messages.error(request, "Informe um nome para o grupo.")
        elif len(name) > 100:
            messages.error(request, "O nome deve ter no máximo 100 caracteres.")
        elif Group.objects.filter(creator=request.user, name__iexact=name).exists():
            messages.error(request, "Você já tem um grupo com esse nome.")
        else:
            new_group = Group.objects.create(name=name, creator=request.user)
            Participant.objects.get_or_create(group=new_group, user=request.user)
            messages.success(request, "Grupo criado com sucesso!")
            return redirect("rachais:group_detail", group_id=new_group.id)

        return render(
            request,
            "rachais/create_group.html",
            {"groups": groups, "name": name},
        )

    return render(request, "rachais/create_group.html", {"groups": groups})


@login_required
def add_participant(request, group_id):
    group = get_object_or_404(Group, pk=group_id)

    if request.user != group.creator:
        messages.error(request, "Apenas o criador do grupo pode adicionar participantes.")
        return redirect("rachais:group_detail", group_id=group.id)

    if request.method == "POST":
        ident = (request.POST.get("identifier") or "").strip()

        if not ident:
            messages.error(request, "Informe o username ou e-mail do usuário.")
            return redirect("rachais:group_detail", group_id=group.id)

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
