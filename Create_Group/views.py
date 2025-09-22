from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
def create_group(request):
    # Esta é uma função de teste. Ela retorna uma resposta HTTP simples.
    # Mais tarde, você irá adicionar a lógica real aqui.
    return HttpResponse("<h1>Esta é a página para criar um grupo.</h1>")