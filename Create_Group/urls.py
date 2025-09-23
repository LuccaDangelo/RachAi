from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_group, name='create_group'),
    path('<int:group_id>/',views.group_detail,name='group_detail'),
]