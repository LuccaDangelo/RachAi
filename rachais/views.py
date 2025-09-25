from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Group, Participant
from .forms import GroupForm

def home(request):
    if request.user.is_authenticated:
        return redirect('rachais:group_list')
    return render (request,'rachais/home.html')

def login(request):
    if request.user.is_authenticated:
        return redirect('rachais:group_list')
    return render (request,'rachais/login.html')

@login_required
def group_list(request):
    groups = Group.objects.all().order_by('-created_at')
    return render(request, 'rachais/group_list.html', {'groups': groups})

@login_required
def group_detail(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    return render(request, 'rachais/group_detail.html', {'group': group})

@login_required
def create_group(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            new_group = form.save(commit=False)
            new_group.creator = request.user
            new_group.save()
            Participant.objects.get_or_create(group=new_group, user=request.user)
            return redirect('rachais:group_detail', group_id=new_group.id)
    else:
        form = GroupForm()
    return render(request, 'rachais/create_group.html', {'form': form})
