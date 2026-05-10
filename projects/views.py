from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from core.constants import (
    PROJECTS_PER_PAGE,
    SKILL_NAME_MAX_LENGTH,
)
from core.services import paginate_queryset, query_prefix
from projects.forms import ProjectForm
from projects.models import Project, Skill
from projects.services import (
    can_manage_project,
    get_or_create_skill,
    project_list_queryset,
    project_queryset,
    request_payload,
    skill_names_queryset,
    skill_suggestions_queryset,
)


def project_list(request):
    active_skill = request.GET.get("skill") or ""
    projects = project_list_queryset(active_skill)

    return render(
        request,
        "projects/project_list.html",
        {
            "projects": projects,
            "page_obj": paginate_queryset(request, projects, PROJECTS_PER_PAGE),
            "all_skills": skill_names_queryset(),
            "active_skill": active_skill,
            "query_prefix": query_prefix(request),
        },
    )


def project_detail(request, pk):
    project = get_object_or_404(project_queryset(), pk=pk)
    return render(request, "projects/project-details.html", {"project": project})


@login_required
def create_project(request):
    form = ProjectForm(request.POST or None)
    if form.is_valid():
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
    if not can_manage_project(request.user, project):
        return HttpResponseForbidden("Недостаточно прав для редактирования проекта.")

    form = ProjectForm(request.POST or None, instance=project)
    if form.is_valid():
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
    if not can_manage_project(request.user, project):
        return JsonResponse(
            {"status": "error", "message": "forbidden"},
            status=HTTPStatus.FORBIDDEN,
        )

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

    if is_participant := project.participants.filter(pk=request.user.pk).exists():
        project.participants.remove(request.user)
    else:
        project.participants.add(request.user)

    return JsonResponse({"status": "ok", "participant": not is_participant})


@require_GET
def skill_autocomplete(request):
    search_query = (request.GET.get("q") or "").strip()
    data = list(skill_suggestions_queryset(search_query))
    return JsonResponse(data, safe=False)


@require_POST
@login_required
def add_project_skill(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not can_manage_project(request.user, project):
        return JsonResponse(
            {"status": "error", "message": "forbidden"},
            status=HTTPStatus.FORBIDDEN,
        )

    payload = request_payload(request)
    skill_id = payload.get("skill_id")
    name = (payload.get("name") or "").strip()

    if skill_id:
        skill = get_object_or_404(Skill, pk=skill_id)
        created = False
    elif name:
        if len(name) > SKILL_NAME_MAX_LENGTH:
            return HttpResponseBadRequest("Skill name is too long.")
        skill, created = get_or_create_skill(name)
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
    if not can_manage_project(request.user, project):
        return JsonResponse(
            {"status": "error", "message": "forbidden"},
            status=HTTPStatus.FORBIDDEN,
        )

    skill = get_object_or_404(Skill, pk=skill_id)
    if not project.skills.filter(pk=skill.pk).exists():
        return JsonResponse(
            {"status": "error", "message": "not attached"},
            status=HTTPStatus.BAD_REQUEST,
        )

    project.skills.remove(skill)
    return JsonResponse({"status": "ok", "removed": True})
