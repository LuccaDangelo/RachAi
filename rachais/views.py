from decimal import Decimal, InvalidOperation
import decimal
from typing import Optional
from collections import defaultdict
from types import SimpleNamespace
from django.db import transaction
from .models import Group, Participant, Expense, ExpenseSplit
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
    
    balances = defaultdict(Decimal)

    all_splits = ExpenseSplit.objects.filter(
        expense__in=expenses
    ).select_related('user')

    splits_by_expense = defaultdict(list)
    for split in all_splits:
        splits_by_expense[split.expense_id].append(split)

    for expense in expenses:
        balances[expense.paid_by.id] += expense.amount

        splits_for_this_expense = splits_by_expense.get(expense.id, [])

        for split in splits_for_this_expense:
            balances[split.user.id] -= split.amount_owed

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
    all_splits = ExpenseSplit.objects.filter(
        expense__in=expenses
    ).select_related('user')
    
    splits_by_expense = defaultdict(list)
    for split in all_splits:
        splits_by_expense[split.expense_id].append(split)

    for e in expenses:
        setattr(e, "paid_by_name", _display_name(e.paid_by))
        
        split_list = []
        splits_for_this_expense = splits_by_expense.get(e.id, [])
        
        for split in splits_for_this_expense:
            if split.user.id == e.paid_by_id:
                continue 
                
            split_list.append({
                "name": _display_name(split.user), 
                "amount": split.amount_owed 
            })
            
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
        }
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
    context = {
        "group": group,
        "participants": participants,
        "submitted_data": request.POST or {}
    }

    if request.method == "POST":
        description = (request.POST.get("description") or "").strip()
        raw_amount = (request.POST.get("amount") or "").strip()
        paid_by_id = request.POST.get("paid_by")
        split_method = request.POST.get("split_method", "EQUAL") 

        if not description:
            messages.error(request, "Informe a descrição da despesa.")
            return render(request, "rachais/add_expense.html", context)

        norm = raw_amount.replace(".", "").replace(",", ".")
        try:
            amount = Decimal(norm) 
        except (InvalidOperation, AttributeError):
            messages.error(request, "Informe um valor válido (ex.: 100,00).")
            return render(request, "rachais/add_expense.html", context)

        if amount <= 0:
            messages.error(request, "O valor da despesa deve ser maior que zero")
            return render(request, "rachais/add_expense.html", context)

        try:
            payer = User.objects.get(pk=paid_by_id)
        except (User.DoesNotExist, ValueError, TypeError):
            messages.error(request, "Selecione quem pagou.")
            return render(request, "rachais/add_expense.html", context) 

        if not Participant.objects.filter(group=group, user=payer).exists():
            messages.error(request, "O pagador precisa ser participante do grupo.")
            return render(request, "rachais/add_expense.html", context) 

        participant_users = [p.user for p in participants]

       
        if split_method == 'EQUAL':
            n_participants = len(participant_users)
            if n_participants == 0:
                messages.error(request, "Não há participantes no grupo para dividir.")
                return render(request, "rachais/add_expense.html", context)

            split_amount = round(amount / n_participants, 2)
            remainder = amount - (split_amount * n_participants)

            try:
                with transaction.atomic():
                    expense = Expense.objects.create(
                        group=group,
                        description=description,
                        amount=amount,
                        paid_by=payer,
                        split_method=split_method
                    )
                    
                    splits_to_create = []
                    for i, user in enumerate(participant_users):
                        amount_owed = split_amount
                        if i == 0: 
                            amount_owed += remainder
                        
                        splits_to_create.append(
                            ExpenseSplit(
                                expense=expense,
                                user=user,
                                amount_owed=amount_owed
                            )
                        )
                    ExpenseSplit.objects.bulk_create(splits_to_create)
                
                messages.success(request, "Despesa registrada com sucesso.")
                return redirect("rachais:group_detail", group_id=group.id)

            except Exception as e:
                messages.error(request, f"Erro ao salvar: {e}")
                return render(request, "rachais/add_expense.html", context)

        elif split_method == 'UNEQUAL_VALUE':
            total_split_sum = Decimal('0.00')
            splits_data_to_save = [] 

            for user in participant_users:
                field_name = f'split_user_{user.id}'
                raw_value = (request.POST.get(field_name) or "0").strip()
                norm_value = raw_value.replace(".", "").replace(",", ".")
                
                try:
                    value_decimal = Decimal(norm_value)
                    if value_decimal < 0:
                        raise InvalidOperation("Valor não pode ser negativo")
                except (InvalidOperation, AttributeError):
                    messages.error(request, f"Valor inválido inserido para {user.username}.")
                    return render(request, "rachais/add_expense.html", context)

                total_split_sum += value_decimal
                splits_data_to_save.append((user, value_decimal))

            if total_split_sum.quantize(Decimal("0.01")) != amount.quantize(Decimal("0.01")):
                error_msg = (
                    f"A soma das partes (R$ {total_split_sum:.2f}) não corresponde "
                    f"ao valor total da despesa (R$ {amount:.2f})"
                )
                messages.error(request, error_msg)
                return render(request, "rachais/add_expense.html", context)
            
            try:
                with transaction.atomic():
                    expense = Expense.objects.create(
                        group=group,
                        description=description,
                        amount=amount,
                        paid_by=payer,
                        split_method=split_method
                    )
                    
                    splits_to_create = []
                    for user, amount_owed in splits_data_to_save:
                        if amount_owed > 0:
                            splits_to_create.append(
                                ExpenseSplit(
                                    expense=expense,
                                    user=user,
                                    amount_owed=amount_owed
                                )
                            )
                    ExpenseSplit.objects.bulk_create(splits_to_create)
                
                messages.success(request, "Despesa registrada com sucesso.")
                return redirect("rachais:group_detail", group_id=group.id)

            except Exception as e:
                messages.error(request, f"Erro ao salvar: {e}")
                return render(request, "rachais/add_expense.html", context)

        elif split_method == 'UNEQUAL_PERCENTAGE':
            total_percentage_sum = Decimal('0.00')
            perc_data_to_save = [] 

            for user in participant_users:
                field_name = f'split_perc_{user.id}'
                raw_perc = (request.POST.get(field_name) or "0").strip()
                norm_perc = raw_perc.replace(".", "").replace(",", ".")
                
                try:
                    perc_decimal = Decimal(norm_perc)
                    if perc_decimal < 0:
                        raise InvalidOperation("Porcentagem não pode ser negativa")
                except (InvalidOperation, AttributeError):
                    messages.error(request, f"Porcentagem inválida para {user.username}.")
                    return render(request, "rachais/add_expense.html", context)

                total_percentage_sum += perc_decimal
                perc_data_to_save.append((user, perc_decimal))
            
            if total_percentage_sum.quantize(Decimal("0.01")) != Decimal('100.00'):
                error_msg = (
                    f"A soma das porcentagens ({total_percentage_sum:.2f}%) não é "
                    f"exatamente 100%"
                )
                messages.error(request, error_msg)
                return render(request, "rachais/add_expense.html", context)
            
            try:
                with transaction.atomic():
                    expense = Expense.objects.create(
                        group=group,
                        description=description,
                        amount=amount,
                        paid_by=payer,
                        split_method=split_method
                    )
                    
                    splits_to_create = []
                    total_calculated_amount = Decimal('0.00')
                    
                    for i, (user, percentage) in enumerate(perc_data_to_save):
                        amount_owed = (percentage / Decimal('100.00') * amount).quantize(Decimal("0.01"))
                        total_calculated_amount += amount_owed

                        if amount_owed > 0:
                            splits_to_create.append(
                                ExpenseSplit(
                                    expense=expense,
                                    user=user,
                                    amount_owed=amount_owed
                                )
                            )
                    remainder = amount - total_calculated_amount
                    if remainder != Decimal('0.00') and splits_to_create:
                        splits_to_create[0].amount_owed += remainder

                    ExpenseSplit.objects.bulk_create(splits_to_create)
                
                messages.success(request, "Despesa registrada com sucesso.")
                return redirect("rachais:group_detail", group_id=group.id)

            except Exception as e:
                messages.error(request, f"Erro ao salvar: {e}")
                return render(request, "rachais/add_expense.html", context)

        else:
            messages.error(request, "Método de divisão inválido.")
            return render(request, "rachais/add_expense.html", context)


    return render(request, "rachais/add_expense.html", context)