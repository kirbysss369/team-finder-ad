from django.urls import path

from projects import views

app_name = "projects"

urlpatterns = [
    path("list/", views.project_list, name="list"),
    path("create-project/", views.create_project, name="create"),
    path("skills/", views.skill_autocomplete, name="skills"),
    path("<int:pk>/", views.project_detail, name="detail"),
    path("<int:pk>/edit/", views.edit_project, name="edit"),
    path("<int:pk>/complete/", views.complete_project, name="complete"),
    path(
        "<int:pk>/toggle-participate/",
        views.toggle_participate,
        name="toggle_participate",
    ),
    path("<int:pk>/skills/add/", views.add_project_skill, name="add_skill"),
    path(
        "<int:pk>/skills/<int:skill_id>/remove/",
        views.remove_project_skill,
        name="remove_skill",
    ),
]
