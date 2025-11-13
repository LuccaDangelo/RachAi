from django.contrib.auth.models import User
from django.db import models
from django.db.models.functions import Lower  # <-- novo
from django.utils import timezone

class Group(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nome do Grupo")  # <- sem unique=True
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("name"), "creator",
                name="uniq_group_name_per_creator_ci"
            )
        ]

    def __str__(self):
        return self.name


class Participant(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_participations')

    def __str__(self):
        return f"{self.user.username} ({self.group.name})"

    class Meta:
        unique_together = ('group', 'user')


class Expense(models.Model):
    """Representa uma despesa registrada em um grupo."""
    SPLIT_METHOD_CHOICES= [
        ('EQUAL','Dividir igualmente'),
        ('UNEQUAL_VALUE','Dividir por valores exatos'),
        ('UNEQUAL_PERCENTAGE','Dividir por porcentagem'),
    ]
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='expenses')
    description = models.CharField(max_length=255, verbose_name="Descrição da Despesa")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    paid_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='paid_expenses', verbose_name="Quem pagou")
    created_at = models.DateTimeField(auto_now_add=True)

    split_method=models.CharField(
        max_length=20,
        choices=SPLIT_METHOD_CHOICES,
        default='EQUAL'
    )
    participants=models.ManyToManyField(
        User,
        through='ExpenseSplit',
        related_name='expenses_participated'
    )
    def __str__(self):
        return f"{self.description} (R$ {self.amount}) em {self.group.name}"

    class Meta:
        verbose_name = "Despesa"
        verbose_name_plural = "Despesas"
        ordering = ['-created_at']
class ExpenseSplit(models.Model):
    expense=models.ForeignKey(Expense,on_delete=models.CASCADE,related_name='splits')
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='splits')
    amount_owed=models.DecimalField(max_digits=10, decimal_places=2,verbose_name="valor devido ")

    class Meta:
        unique_together=('expense','user')
    def __str__(self):
        return f"{self.user.username} deve R$ {self.amount_owed} para {self.expense.description}"

class Payment(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="payments")
    payer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments_made")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments_received")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments_registered")
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.payer} pagou R$ {self.amount} para {self.receiver} em {self.group}"
    