from users.models import User


def participant_queryset():
    return User.objects.filter(is_active=True).order_by("-id")


def profile_queryset():
    return User.objects.prefetch_related("owned_projects__participants")
