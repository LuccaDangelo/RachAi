from django.urls import path
from . import views

app_name = "rachais"  # <-- namespace

urlpatterns = [
    path("", views.home, name="home"),
    path("groups/", views.group_list, name="group_list"),
    path("groups/create/", views.create_group, name="create_group"),
    path("groups/<int:group_id>/", views.group_detail, name="group_detail"),
]
