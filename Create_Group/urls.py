from django.urls import path
from . import views

urlpatterns = [
    # /Group/  -> lista
    path('', views.group_list, name='group_list'),

    # /Group/create/ -> criar
    path('create/', views.create_group, name='create_group'),

    # /Group/42/ -> detalhe
    path('<int:group_id>/', views.group_detail, name='group_detail'),
]
