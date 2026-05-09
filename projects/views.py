import json

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from .forms import ProjectForm
from .models import Project, Skill


def project_list(request):
    active_skill = request.GET.get("skill") or ""
    projects = (
        Project.objects.select_related("owner")
        .prefetch_related("participants", "skills")
        .order_by("-created_at")
    )

    if active_skill:
        projects = projects.filter(skills__name=active_skill).distinct()

    page_obj = Paginator(projects, 12).get_page(request.GET.get("page"))
    return render(
        request,
        "projects/project_list.html",
        {
            "projects": projects,
            "page_obj": page_obj,
            "all_skills": Skill.objects.order_by("name").values_list("name", flat=True),
            "active_skill": active_skill,
            "query_prefix": _query_prefix(request),
        },
    )


def project_detail(request, pk):
    project = get_object_or_404(
        Project.objects.select_related("owner").prefetch_related(
            "participants",
            "skills",
        ),
        pk=pk,
    )
    return render(request, "projects/project-details.html", {"project": project})


@login_required
def create_project(request):
    form = ProjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()
        project.participants.add(request.user)
        return redirect("projects:detail", pk=project.pk)
    return render(
        request,
        "projects/create-project.html",
        {"form": form, "is_edit": False},
    )


@login_required
def edit_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not _can_manage_project(request.user, project):
        return HttpResponseForbidden("Недостаточно прав для редактирования проекта.")

    form = ProjectForm(request.POST or None, instance=project)
    if request.method == "POST" and form.is_valid():
        project = form.save()
        return redirect("projects:detail", pk=project.pk)
    return render(
        request,
        "projects/create-project.html",
        {"form": form, "is_edit": True},
    )


@require_POST
@login_required
def complete_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not _can_manage_project(request.user, project):
        return JsonResponse({"status": "error", "message": "forbidden"}, status=403)

    if project.status == Project.STATUS_OPEN:
        project.status = Project.STATUS_CLOSED
        project.save(update_fields=["status"])
    return JsonResponse({"status": "ok", "project_status": project.status})


@require_POST
@login_required
def toggle_participate(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.owner_id == request.user.id:
        project.participants.add(request.user)
        return JsonResponse({"status": "ok", "participant": True})

    if project.participants.filter(pk=request.user.pk).exists():
        project.participants.remove(request.user)
        participant = False
    else:
        project.participants.add(request.user)
        participant = True

    return JsonResponse({"status": "ok", "participant": participant})


@require_GET
def skill_autocomplete(request):
    q = (request.GET.get("q") or "").strip()
    skills = Skill.objects.all()
    if q:
        skills = skills.filter(name__istartswith=q)
    data = list(skills.order_by("name").values("id", "name")[:10])
    return JsonResponse(data, safe=False)


@require_POST
@login_required
def add_project_skill(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not _can_manage_project(request.user, project):
        return JsonResponse({"status": "error", "message": "forbidden"}, status=403)

    payload = _request_payload(request)
    skill_id = payload.get("skill_id")
    name = (payload.get("name") or "").strip()

    if skill_id:
        skill = get_object_or_404(Skill, pk=skill_id)
        created = False
    elif name:
        if len(name) > 124:
            return HttpResponseBadRequest("Skill name is too long.")
        skill, created = _get_or_create_skill(name)
    else:
        return HttpResponseBadRequest("skill_id or name is required.")

    added = not project.skills.filter(pk=skill.pk).exists()
    if added:
        project.skills.add(skill)

    return JsonResponse(
        {
            "id": skill.pk,
            "name": skill.name,
            "skill_id": skill.pk,
            "created": created,
            "added": added,
        }
    )


@require_POST
@login_required
def remove_project_skill(request, pk, skill_id):
    project = get_object_or_404(Project, pk=pk)
    if not _can_manage_project(request.user, project):
        return JsonResponse({"status": "error", "message": "forbidden"}, status=403)

    skill = get_object_or_404(Skill, pk=skill_id)
    if not project.skills.filter(pk=skill.pk).exists():
        return JsonResponse({"status": "error", "message": "not attached"}, status=400)

    project.skills.remove(skill)
    return JsonResponse({"status": "ok", "removed": True})


def _can_manage_project(user, project):
    return user.is_authenticated and (user.is_staff or project.owner_id == user.id)


def _get_or_create_skill(name):
    existing = Skill.objects.filter(name__iexact=name).first()
    if existing:
        return existing, False
    return Skill.objects.create(name=name), True


def _request_payload(request):
    # skills.js отправляет JSON, а тесты и простые формы могут передавать POST.
    if request.content_type == "application/json":
        try:
            return json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return {}
    return request.POST


def _query_prefix(request):
    params = request.GET.copy()
    params.pop("page", None)
    encoded = params.urlencode()
    return f"{encoded}&" if encoded else ""
