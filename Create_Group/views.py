from django.contrib.auth.decorators import login_required
from .forms import GroupForm
from django.shortcuts import render, redirect
from .models import Group
from django.shortcuts import render, get_list_or_404
def group_detail(request,group_id):
    group = get_list_or_404(Group, pk=group_id)
    return render (request,'Create_Group/group_detail.html',{'group':group})
@login_required
def create_group(request):
    if request.method == 'POST':
        form = GroupForm(request.POST, request.FILES)
        if form.is_valid():
            new_group = form.save(commit=False)
            new_group.creator = request.user
            new_group.save()
            return redirect('group_detail', group_id=new_group.id)
    else:
        form = GroupForm()

    return render(request, 'Create_Group/create_group.html', {'form': form})