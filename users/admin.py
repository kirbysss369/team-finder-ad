from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.db.models import Count
from django.utils.html import format_html

from core.constants import ADMIN_AVATAR_SIZE
from users.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    list_display = (
        "avatar_preview",
        "email",
        "name",
        "surname",
        "phone",
        "participated_projects_count",
        "is_staff",
        "is_active",
    )
    list_filter = ("is_staff", "is_active")
    ordering = ("email",)
    search_fields = ("email", "name", "surname", "phone")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Личная информация",
            {"fields": ("name", "surname", "avatar", "phone", "github_url", "about")},
        ),
        (
            "Права",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "name",
                    "surname",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                participated_projects_total=Count(
                    "participated_projects",
                    distinct=True,
                )
            )
        )

    @admin.display(description="Аватар")
    def avatar_preview(self, obj):
        if not obj.avatar:
            return "-"
        return format_html(
            '<img src="{}" width="{}" height="{}" '
            'style="object-fit: cover; border-radius: 50%;" />',
            obj.avatar.url,
            ADMIN_AVATAR_SIZE,
            ADMIN_AVATAR_SIZE,
        )

    @admin.display(description="Проекты", ordering="participated_projects_total")
    def participated_projects_count(self, obj):
        return obj.participated_projects_total
