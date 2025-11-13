from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from . import views
from .models import Expense, ExpenseSplit, Group, Participant, Payment


class LoggingMixin:
    """Imprime as etapas durante a execução das suites de teste."""

    def log_stage(self, etapa: str, mensagem: str) -> None:
        print(f"[TESTE] {self.__class__.__name__} | {etapa}: {mensagem}")

    def log_success(self, etapa: str, mensagem: str) -> None:
        print(f"[TESTE][OK] {self.__class__.__name__} | {etapa}: {mensagem}")


# Classe base que prepara usuários e um grupo padrão para reaproveitar nos testes.
class BaseRachaiTestCase(LoggingMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.log_stage("setup", "Criando usuários e grupo base.")
        user_model = get_user_model()
        self.creator = user_model.objects.create_user(
            username="creator",
            email="creator@example.com",
            password="pass123",
            first_name="Criador",
        )
        self.member = user_model.objects.create_user(
            username="membro",
            email="member@example.com",
            password="pass123",
            first_name="Membro",
        )
        self.other_user = user_model.objects.create_user(
            username="outsider",
            email="outsider@example.com",
            password="pass123",
            first_name="Visitante",
        )
        self.group = Group.objects.create(name="Viagem Base", creator=self.creator)
        Participant.objects.create(group=self.group, user=self.creator)
        Participant.objects.create(group=self.group, user=self.member)
        self.log_success("setup", "Usuários e grupo configurados.")


# Testa as diversas quedas de _display_name para montar nomes exibíveis.
class DisplayNameHelperTests(LoggingMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user_model = get_user_model()

    def test_display_name_prefers_full_name(self):
        # Deve priorizar o nome completo quando presente.
        self.log_stage("display_name", "Validando prioridade do nome completo.")
        user = self.user_model.objects.create_user(
            username="pref",
            email="pref@example.com",
            password="pass123",
            first_name="Ignored",
            last_name="AlsoIgnored",
        )
        user.first_name = ""
        user.last_name = ""
        user.save()
        user.get_full_name = lambda: "Nome Completo"  # type: ignore

        self.assertEqual(views._display_name(user), "Nome Completo")
        self.log_success("display_name", "Nome completo escolhido corretamente.")

    def test_display_name_falls_back_to_username_prefix(self):
        # Caso contrário, deve usar o prefixo do username (antes do @).
        self.log_stage("display_name", "Verificando fallback para prefixo do username.")
        user = self.user_model.objects.create_user(
            username="emailuser@example.com",
            email="emailuser@example.com",
            password="pass123",
        )
        user.first_name = ""
        user.save()
        self.assertEqual(views._display_name(user), "emailuser")
        self.log_success("display_name", "Fallback para prefixo realizado.")


class SidebarQueryTests(BaseRachaiTestCase):
    def test_sidebar_includes_groups_created_and_joined(self):
        # Sidebar precisa listar grupos que o usuário criou e também os que participa.
        self.log_stage("sidebar", "Coletando grupos criados e participados.")
        extra_group = Group.objects.create(name="Outros Planos", creator=self.other_user)
        Participant.objects.create(group=extra_group, user=self.member)

        qs = views._sidebar_groups_qs(self.member)
        names = list(qs.values_list("name", flat=True))

        self.assertIn(self.group.name, names)
        self.assertIn(extra_group.name, names)
        self.log_success("sidebar", "Sidebar retornou todos os grupos esperados.")


class HelperFunctionTests(BaseRachaiTestCase):
    def setUp(self):
        super().setUp()
        self.log_stage("helper_setup", "Criando despesa, splits e pagamento iniciais.")
        self.expense = Expense.objects.create(
            group=self.group,
            description="Hotel",
            amount=Decimal("100.00"),
            paid_by=self.creator,
            split_method="UNEQUAL_VALUE",
        )
        ExpenseSplit.objects.create(
            expense=self.expense,
            user=self.creator,
            amount_owed=Decimal("20.00"),
        )
        ExpenseSplit.objects.create(
            expense=self.expense,
            user=self.member,
            amount_owed=Decimal("80.00"),
        )
        Payment.objects.create(
            group=self.group,
            payer=self.member,
            receiver=self.creator,
            amount=Decimal("30.00"),
            created_by=self.member,
        )
        self.log_success("helper_setup", "Fixtures específicas criadas.")

    def test_calculate_balances_includes_payments(self):
        # Balanços devem considerar tanto despesas quanto pagamentos registrados.
        self.log_stage("balances", "Executando _calculate_balances com pagamento feito.")
        balances = views._calculate_balances(self.group)
        self.assertEqual(balances[self.creator.id], Decimal("50.00"))
        self.assertEqual(balances[self.member.id], Decimal("-50.00"))
        self.log_success("balances", "Balanços refletiram despesas e pagamentos.")

    def test_calculate_settlements_pairs_creditors_and_debtors(self):
        # Settlements devem formar pares corretos credor/devedor.
        self.log_stage("settlements", "Montando pares credor/devedor.")
        balances = views._calculate_balances(self.group)
        participants = list(self.group.participants.select_related("user"))
        settlements = views._calculate_settlements(balances, participants)

        self.assertEqual(len(settlements), 1)
        settlement = settlements[0]
        self.assertEqual(settlement.person_from, self.member)
        self.assertEqual(settlement.person_to, self.creator)
        self.assertEqual(settlement.amount, Decimal("50.00"))
        self.log_success("settlements", "Pares encontrados corretamente.")

    def test_my_debts_snapshot_lists_pending_and_paid(self):
        # Snapshot usado no dashboard precisa separar pendências e pagamentos feitos.
        self.log_stage("snapshot", "Coletando pendências e pagamentos do membro.")
        snapshot = views._my_debts_snapshot(self.member)
        self.assertEqual(len(snapshot["pending_to_pay"]), 1)
        self.assertEqual(snapshot["pending_to_receive"], [])
        self.assertEqual(snapshot["paid"][0].amount, Decimal("30.00"))
        self.log_success("snapshot", "Pendências e pagamentos listados corretamente.")


class CreateGroupViewTests(BaseRachaiTestCase):
    def test_create_group_successfully_registers_creator(self):
        # Fluxo feliz: cria grupo e já adiciona o criador como participante.
        self.log_stage("create_group", "Iniciando fluxo feliz de criação.")
        self.client.force_login(self.creator)
        response = self.client.post(reverse("rachais:create_group"), {"name": "Nova Trip"})

        new_group = Group.objects.get(name="Nova Trip")
        self.assertRedirects(
            response, reverse("rachais:group_detail", args=[new_group.id])
        )
        self.assertEqual(new_group.creator, self.creator)
        self.assertTrue(
            Participant.objects.filter(group=new_group, user=self.creator).exists()
        )
        self.log_success("create_group", "Criador redirecionado e incluído no grupo novo.")

    def test_create_group_rejects_duplicate_name_per_creator(self):
        # Deve impedir nomes duplicados para o mesmo criador (case insensitive).
        self.log_stage("create_group", "Testando bloqueio de nome duplicado.")
        Group.objects.create(name="Duplicado", creator=self.creator)
        self.client.force_login(self.creator)

        response = self.client.post(reverse("rachais:create_group"), {"name": "duplicado"})

        self.assertEqual(
            Group.objects.filter(creator=self.creator, name__iexact="duplicado").count(),
            1,
        )
        self.assertEqual(response.status_code, 200)
        self.log_success("create_group", "Nome duplicado foi rejeitado.")


class AddParticipantViewTests(BaseRachaiTestCase):
    def test_only_creator_can_add_participants(self):
        # Somente o criador pode adicionar novos usuários ao grupo.
        self.log_stage("add_participant", "Tentando adicionar participante sem ser criador.")
        self.client.force_login(self.member)
        response = self.client.post(
            reverse("rachais:add_participant", args=[self.group.id]),
            {"identifier": self.other_user.email},
        )

        self.assertRedirects(
            response, reverse("rachais:group_detail", args=[self.group.id])
        )
        self.assertFalse(
            Participant.objects.filter(group=self.group, user=self.other_user).exists()
        )
        self.log_success("add_participant", "Bloqueio para não-criador funcionou.")

    def test_creator_can_add_participant_by_email(self):
        # Criador consegue adicionar participante informando e-mail.
        self.log_stage("add_participant", "Criador adicionando novo participante por e-mail.")
        self.client.force_login(self.creator)
        response = self.client.post(
            reverse("rachais:add_participant", args=[self.group.id]),
            {"identifier": self.other_user.email},
        )

        self.assertRedirects(
            response, reverse("rachais:group_detail", args=[self.group.id])
        )
        self.assertTrue(
            Participant.objects.filter(group=self.group, user=self.other_user).exists()
        )
        self.log_success("add_participant", "Participante adicionado com sucesso.")


class AddExpenseViewTests(BaseRachaiTestCase):
    def _expense_url(self):
        return reverse("rachais:add_expense", args=[self.group.id])

    def test_non_participant_cannot_add_expense(self):
        # Usuários fora do grupo não podem registrar despesas.
        self.log_stage("add_expense", "Usuário externo tentando adicionar despesa.")
        self.client.force_login(self.other_user)
        response = self.client.post(
            self._expense_url(),
            {
                "description": "Jantar",
                "amount": "100,00",
                "paid_by": str(self.creator.id),
                "split_method": "EQUAL",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("rachais:group_detail", args=[self.group.id])
        )
        self.assertEqual(Expense.objects.count(), 0)
        self.log_success("add_expense", "Tentativa barrada para usuário fora do grupo.")

    def test_equal_split_expense_creates_even_splits(self):
        # Divisão igual deve dividir o valor linearmente entre participantes.
        self.log_stage("add_expense", "Registrando despesa com divisão igual.")
        self.client.force_login(self.creator)
        response = self.client.post(
            self._expense_url(),
            {
                "description": "Jantar",
                "amount": "150,00",
                "paid_by": str(self.creator.id),
                "split_method": "EQUAL",
            },
        )
        self.assertRedirects(
            response, reverse("rachais:group_detail", args=[self.group.id])
        )
        expense = Expense.objects.get(description="Jantar")
        splits = {
            split.user_id: split.amount_owed for split in expense.splits.all()
        }
        self.assertEqual(splits[self.creator.id], Decimal("75.00"))
        self.assertEqual(splits[self.member.id], Decimal("75.00"))
        self.log_success("add_expense", "Divisão igual calculada corretamente.")

    def test_unequal_value_split_respects_submitted_values(self):
        # Divisão por valor exato deve respeitar os campos informados.
        self.log_stage("add_expense", "Registrando despesa por valores exatos.")
        self.client.force_login(self.creator)
        response = self.client.post(
            self._expense_url(),
            {
                "description": "Mercado",
                "amount": "150,00",
                "paid_by": str(self.member.id),
                "split_method": "UNEQUAL_VALUE",
                f"split_user_{self.creator.id}": "100,00",
                f"split_user_{self.member.id}": "50,00",
            },
        )
        self.assertRedirects(
            response, reverse("rachais:group_detail", args=[self.group.id])
        )
        expense = Expense.objects.get(description="Mercado")
        splits = {
            split.user_id: split.amount_owed for split in expense.splits.all()
        }
        self.assertEqual(splits[self.creator.id], Decimal("100.00"))
        self.assertEqual(splits[self.member.id], Decimal("50.00"))
        self.log_success("add_expense", "Valores exatos respeitados.")

    def test_unequal_value_split_validates_total(self):
        # Soma dos valores precisa bater com o total, senão exibe erro.
        self.log_stage("add_expense", "Validando erro de soma incorreta em valores exatos.")
        self.client.force_login(self.creator)
        response = self.client.post(
            self._expense_url(),
            {
                "description": "Erro",
                "amount": "150,00",
                "paid_by": str(self.creator.id),
                "split_method": "UNEQUAL_VALUE",
                f"split_user_{self.creator.id}": "80,00",
                f"split_user_{self.member.id}": "60,00",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Expense.objects.filter(description="Erro").exists())
        self.log_success("add_expense", "Erro exibido quando soma não bateu.")

    def test_percentage_split_saves_quantized_amounts(self):
        # Divisão percentual deve quantizar corretamente e salvar splits.
        self.log_stage("add_expense", "Registrando despesa por porcentagem.")
        self.client.force_login(self.creator)
        response = self.client.post(
            self._expense_url(),
            {
                "description": "Combustível",
                "amount": "300,00",
                "paid_by": str(self.creator.id),
                "split_method": "UNEQUAL_PERCENTAGE",
                f"split_perc_{self.creator.id}": "25",
                f"split_perc_{self.member.id}": "75",
            },
        )
        self.assertRedirects(
            response, reverse("rachais:group_detail", args=[self.group.id])
        )
        expense = Expense.objects.get(description="Combustível")
        splits = {
            split.user_id: split.amount_owed for split in expense.splits.all()
        }
        self.assertEqual(splits[self.creator.id], Decimal("75.00"))
        self.assertEqual(splits[self.member.id], Decimal("225.00"))
        self.log_success("add_expense", "Percentuais aplicados corretamente.")


class PayDebtViewTests(BaseRachaiTestCase):
    def _create_debt(self, amount=Decimal("120.00")):
        expense = Expense.objects.create(
            group=self.group,
            description="Viagem",
            amount=amount,
            paid_by=self.creator,
            split_method="EQUAL",
        )
        ExpenseSplit.objects.create(
            expense=expense,
            user=self.creator,
            amount_owed=Decimal("0.00"),
        )
        ExpenseSplit.objects.create(
            expense=expense,
            user=self.member,
            amount_owed=amount,
        )
        return expense

    def test_pay_debt_creates_payment_when_amount_matches(self):
        # Ao pagar o valor exato da dívida, deve registrar Payment.
        self.log_stage("pay_debt", "Tentando registrar pagamento com valor correto.")
        self._create_debt()
        self.client.force_login(self.member)
        response = self.client.post(
            reverse("rachais:pay_debt"),
            {
                "group_id": str(self.group.id),
                "receiver_id": str(self.creator.id),
                "amount": "120.00",
            },
        )
        self.assertRedirects(
            response, reverse("rachais:group_detail", args=[self.group.id])
        )
        payment = Payment.objects.get()
        self.assertEqual(payment.payer, self.member)
        self.assertEqual(payment.receiver, self.creator)
        self.assertEqual(payment.amount, Decimal("120.00"))
        self.log_success("pay_debt", "Pagamento registrado com valor esperado.")

    def test_pay_debt_rejects_when_amount_differs_from_settlement(self):
        # Valor divergente do settlement não pode gerar Payment.
        self.log_stage("pay_debt", "Tentando registrar pagamento com valor divergente.")
        self._create_debt()
        self.client.force_login(self.member)
        response = self.client.post(
            reverse("rachais:pay_debt"),
            {
                "group_id": str(self.group.id),
                "receiver_id": str(self.creator.id),
                "amount": "50.00",
            },
        )
        self.assertRedirects(
            response, reverse("rachais:group_detail", args=[self.group.id])
        )
        self.assertEqual(Payment.objects.count(), 0)
        self.log_success("pay_debt", "Pagamento incorreto foi bloqueado.")
