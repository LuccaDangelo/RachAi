from django.contrib.auth.models import User
from django.db import models


class Group(models.Model):

    name = models.CharField(max_length=100, unique=True, verbose_name="Nome do Grupo")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='expenses')
    description = models.CharField(max_length=255, verbose_name="Descrição da Despesa")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    paid_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='paid_expenses')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description} (R$ {self.amount}) em {self.group.name}"
    
    class Meta:
        verbose_name = "Despesa"
        verbose_name_plural = "Despesas"