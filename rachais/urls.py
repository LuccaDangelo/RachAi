from django.urls import path
from . import views

app_name = "rachais"

urlpatterns = [
    path("", views.group_list, name="group_list"),
    path("home/", views.group_list, name="home"),
    path("groups/", views.group_list, name="group_list"),
    path("groups/create/", views.create_group, name="create_group"),
    path("groups/<int:group_id>/", views.group_detail, name="group_detail"),
    path("groups/<int:group_id>/add-participant/", views.add_participant, name="add_participant"),
    path("groups/<int:group_id>/expenses/add/", views.add_expense, name="add_expense"),
]
