from django.shortcuts import render, redirect, get_object_or_404
from .models import Group
from .forms import GroupForm 

''''listar todos os grupos'''
def group_list(request):
    groups = Group.objects.all().order_by('-created_at')
    return render(request, 'Create_Group/group_list.html', {'groups': groups})
''''pagina detalhada dos grupos'''
def group_detail(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    return render(request, 'Create_Group/group_detail.html', {'group': group})
'''criar um novo grupo view'''
def create_group(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            new_group = form.save()
            return redirect('group_detail', group_id=new_group.id)
    else:
        form = GroupForm()

    return render(request, 'Create_Group/create_group.html', {'form': form})