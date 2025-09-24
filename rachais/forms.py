from django import forms
from .models import Group

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']
        labels = {
            'name': 'Nome do Grupo' 
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ex: Viagem para a Praia'}) 
        }