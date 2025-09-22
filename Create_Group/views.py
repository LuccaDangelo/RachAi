from django.shortcuts import render,redirect
from .models import Group
from .forms import GroupForm

# Create your views here.
def create_group(request):
    '''View para criar um novo grupo de despesas'''
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            group = form.save()
            '''Redireciona para a página de detalhes do grupo após a criação'''
            return redirect('group_detail', group_id=group.id)
    else:
        '''Se a requisição não for POST, exibe o formulário vazio'''
        form = GroupForm()

    '''Renderiza o template 'create_group.html' passando o formulário'''
    return render(request, 'create_group/create_group.html', {'form': form})