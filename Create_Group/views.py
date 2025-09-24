from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Group, Participant
from .forms import GroupForm

@login_required
def group_list(request):
    groups = Group.objects.all().order_by('-created_at')
    return render(request, 'Create_Group/group_list.html', {'groups': groups})

@login_required
def group_detail(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    return render(request, 'Create_Group/group_detail.html', {'group': group})

@login_required
def create_group(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            new_group = form.save(commit=False)
            new_group.creator = request.user
            new_group.save()
            Participant.objects.get_or_create(group=new_group, user=request.user)
            return redirect('group_detail', group_id=new_group.id)
    else:
        form = GroupForm()
    return render(request, 'Create_Group/create_group.html', {'form': form})
