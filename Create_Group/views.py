from django.shortcuts import render
from .forms import GroupForm

# Create your views here.
def create_group(request):
    form = GroupForm()
    return render(request, 'Create_Group/create_group.html', {'form': form})