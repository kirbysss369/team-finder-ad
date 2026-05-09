from django.contrib.auth import (
    login as auth_login,
    logout as auth_logout,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import LoginForm, ProfileForm, RegistrationForm, UserPasswordChangeForm
from .models import User


def participant_list(request):
    participants = User.objects.filter(is_active=True).order_by("-id")
    page_obj = Paginator(participants, 12).get_page(request.GET.get("page"))
    return render(
        request,
        "users/participants.html",
        {
            "participants": participants,
            "page_obj": page_obj,
            "query_prefix": _query_prefix(request),
        },
    )


def user_detail(request, pk):
    profile_user = get_object_or_404(
        User.objects.prefetch_related("owned_projects__participants"),
        pk=pk,
        is_active=True,
    )
    return render(request, "users/user-details.html", {"user": profile_user})


def register(request):
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        auth_login(request, user)
        return redirect("projects:list")
    return render(request, "users/register.html", {"form": form})


def login(request):
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        auth_login(request, form.get_user())
        return redirect("projects:list")
    return render(request, "users/login.html", {"form": form})


def logout(request):
    auth_logout(request)
    return redirect("projects:list")


@login_required
def edit_profile(request):
    form = ProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=request.user,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("users:detail", pk=request.user.pk)
    return render(request, "users/edit_profile.html", {"form": form})


@login_required
def change_password(request):
    form = UserPasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        return redirect("users:detail", pk=user.pk)
    return render(request, "users/change_password.html", {"form": form})


def _query_prefix(request):
    params = request.GET.copy()
    params.pop("page", None)
    encoded = params.urlencode()
    return f"{encoded}&" if encoded else ""
