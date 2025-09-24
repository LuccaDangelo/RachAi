from django.contrib import admin

from rachais.models import Expense, Group, Participant

# Register your models here.
admin.site.register(Group)
admin.site.register(Participant)
admin.site.register(Expense)
