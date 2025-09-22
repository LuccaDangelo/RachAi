from django.shortcuts import render
from Create_Group.forms import GroupForm
# Create your views here.
def create_group(request):
    form=GroupForm()
    return render(request,'create_group.html',{'form':form})