from django.db import models

# Create your models here.
class Group(models.Model):
    """Representa um grupo de despesas."""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nome do Grupo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Participant(models.Model):
    """Representa uma pessoa que faz parte de um grupo."""
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='participants')
    name = models.CharField(max_length=100, verbose_name="Nome do Participante")

    def __str__(self):
        return f"{self.name} ({self.group.name})"

    class Meta:
        unique_together = ('group', 'name')
        verbose_name = "Participante"
        verbose_name_plural = "Participantes"

class Expense(models.Model):
    """Representa uma despesa registrada em um grupo."""
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='expenses')
    description = models.CharField(max_length=255, verbose_name="Descrição da Despesa")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    paid_by = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='paid_expenses')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description} (R$ {self.amount}) em {self.group.name}"

    class Meta:
        verbose_name = "Despesa"
        verbose_name_plural = "Despesas"