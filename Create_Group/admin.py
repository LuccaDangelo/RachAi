from django.contrib import admin

from Create_Group.models import Expense, Group, Participant

# Register your models here.
admin.site.register(Group)
admin.site.register(Participant)
admin.site.register(Expense)
