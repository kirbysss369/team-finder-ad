from django.contrib import admin

from projects.models import Project, Skill


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "status",
        "created_at",
        "participants_list",
        "skills_list",
    )
    list_editable = ("status",)
    list_filter = ("status", "created_at", "skills")
    search_fields = (
        "name",
        "description",
        "owner__email",
        "owner__name",
        "owner__surname",
    )
    autocomplete_fields = ("owner", "participants", "skills")
    date_hierarchy = "created_at"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("owner")
            .prefetch_related("participants", "skills")
        )

    @admin.display(description="Участники")
    def participants_list(self, obj):
        return ", ".join(str(user) for user in obj.participants.all()) or "-"

    @admin.display(description="Навыки")
    def skills_list(self, obj):
        return ", ".join(skill.name for skill in obj.skills.all()) or "-"
