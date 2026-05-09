from django.core.management.base import BaseCommand

from projects.models import Project, Skill
from users.models import User


class Command(BaseCommand):
    help = "Create demo users, skills and projects for local review."

    def handle(self, *args, **options):
        # Демо-данные можно безопасно создавать повторно.
        users = [
            {
                "email": "maria@yandex.ru",
                "password": "password",
                "name": "Мария",
                "surname": "Иванова",
                "phone": "+79000000001",
                "github_url": "https://github.com/maria",
                "about": "Backend-разработчик, люблю аккуратные API и pet-проекты.",
            },
            {
                "email": "alex@example.com",
                "password": "password",
                "name": "Алексей",
                "surname": "Петров",
                "phone": "+79000000002",
                "github_url": "https://github.com/alex",
                "about": "Frontend-разработчик, собираю удобные интерфейсы.",
            },
            {
                "email": "olga@example.com",
                "password": "password",
                "name": "Ольга",
                "surname": "Смирнова",
                "phone": "+79000000003",
                "github_url": "https://github.com/olga",
                "about": (
                    "Дизайнер продукта и исследователь пользовательских сценариев."
                ),
            },
        ]

        created_users = {}
        for data in users:
            user_data = data.copy()
            password = user_data.pop("password")
            user, created = User.objects.get_or_create(
                email=user_data["email"],
                defaults=user_data,
            )
            if created:
                user.set_password(password)
                user.save()
            created_users[user.email] = user

        skill_names = [
            "Django",
            "PostgreSQL",
            "JavaScript",
            "UI/UX",
            "Docker",
            "REST API",
        ]
        skills = {
            name: Skill.objects.get_or_create(name=name)[0]
            for name in skill_names
        }

        projects = [
            {
                "owner": created_users["maria@yandex.ru"],
                "name": "API для книжного клуба",
                "description": (
                    "Сервис для обсуждения книг, списков чтения и рекомендаций."
                ),
                "github_url": "https://github.com/maria/book-club-api",
                "skills": ["Django", "PostgreSQL", "REST API"],
            },
            {
                "owner": created_users["alex@example.com"],
                "name": "Планировщик учебных спринтов",
                "description": (
                    "Инструмент для командного планирования небольших учебных "
                    "проектов."
                ),
                "github_url": "https://github.com/alex/sprint-planner",
                "skills": ["JavaScript", "Django", "Docker"],
            },
            {
                "owner": created_users["olga@example.com"],
                "name": "Каталог дизайн-референсов",
                "description": (
                    "Коллекция UI-паттернов с тегами, заметками и командной "
                    "модерацией."
                ),
                "github_url": "https://github.com/olga/design-library",
                "skills": ["UI/UX", "JavaScript"],
            },
        ]

        for data in projects:
            project_data = data.copy()
            project_skills = project_data.pop("skills")
            project, _ = Project.objects.get_or_create(
                owner=project_data["owner"],
                name=project_data["name"],
                defaults=project_data,
            )
            project.participants.add(project_data["owner"])
            project.skills.set([skills[name] for name in project_skills])

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
