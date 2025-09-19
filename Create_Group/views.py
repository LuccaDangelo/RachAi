from django.shortcuts import render

# Create your views here.
def list_groups(request):
 
    fake_groups_data = [
        {'nome': 'Viagem para a Praia', 'descricao': 'Despesas do feriado.'},
        {'nome': 'Contas do Apartamento', 'descricao': 'Aluguel, internet, luz.'},
        {'nome': 'Jantar de Aniversário', 'descricao': 'Comemoração do Rafael.'},
    ]
    context = {
        'page_title': 'Meus Grupos (Dados de Teste)',
        'lista_de_grupos': fake_groups_data,
    }
    return render(request, 'Create_Group/group_list.html', context)