import json

from core.constants import SKILL_AUTOCOMPLETE_LIMIT
from projects.models import Project, Skill


def project_queryset():
    return Project.objects.select_related("owner").prefetch_related(
        "participants",
        "skills",
    )


def project_list_queryset(active_skill):
    projects = project_queryset().order_by("-created_at")
    if active_skill:
        projects = projects.filter(skills__name=active_skill).distinct()
    return projects


def skill_names_queryset():
    return Skill.objects.order_by("name").values_list("name", flat=True)


def skill_suggestions_queryset(search_query):
    skills = Skill.objects.all()
    if search_query:
        skills = skills.filter(name__istartswith=search_query)
    return skills.order_by("name").values("id", "name")[:SKILL_AUTOCOMPLETE_LIMIT]


def can_manage_project(user, project):
    return user.is_authenticated and (user.is_staff or project.owner_id == user.id)


def get_or_create_skill(name):
    existing = Skill.objects.filter(name__iexact=name).first()
    if existing:
        return existing, False
    return Skill.objects.create(name=name), True


def request_payload(request):
    # skills.js отправляет JSON, а тесты и простые формы могут передавать POST.
    if request.content_type == "application/json":
        try:
            return json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return {}
    return request.POST
