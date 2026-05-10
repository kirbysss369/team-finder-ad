import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from projects.models import Project, Skill
from users.models import User

DEFAULT_DATA_PATH = Path(__file__).resolve().parents[2] / "fixtures" / "demo_data.json"


class Command(BaseCommand):
    help = "Create demo users, skills and projects for local review."

    def add_arguments(self, parser):
        parser.add_argument(
            "--data-file",
            default=DEFAULT_DATA_PATH,
            type=Path,
            help="Path to JSON file with demo users, skills and projects.",
        )

    def handle(self, *args, **options):
        data = self._load_data(options["data_file"])

        created_users = {}
        for item in data["users"]:
            user_data = item.copy()
            password = user_data.pop("password")
            user, _ = User.objects.update_or_create(
                email=user_data["email"],
                defaults=user_data,
            )
            user.set_password(password)
            user.save(update_fields=["password"])
            created_users[user.email] = user

        skills = {
            name: Skill.objects.get_or_create(name=name)[0]
            for name in data["skills"]
        }

        for item in data["projects"]:
            project_data = item.copy()
            project_skills = project_data.pop("skills")
            owner_email = project_data.pop("owner_email")
            try:
                owner = created_users[owner_email]
            except KeyError as error:
                raise CommandError(f"Unknown project owner: {owner_email}") from error

            project_data["owner"] = owner
            project, _ = Project.objects.update_or_create(
                owner=owner,
                name=project_data["name"],
                defaults=project_data,
            )
            project.participants.add(owner)

            project_skill_objects = []
            for name in project_skills:
                skill = skills.get(name)
                if skill is None:
                    skill = Skill.objects.get_or_create(name=name)[0]
                    skills[name] = skill
                project_skill_objects.append(skill)
            project.skills.set(project_skill_objects)

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))

    def _load_data(self, data_file):
        try:
            with data_file.open(encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError as error:
            raise CommandError(f"Demo data file not found: {data_file}") from error
        except json.JSONDecodeError as error:
            raise CommandError(f"Invalid demo data JSON: {error}") from error

        for section in ("users", "skills", "projects"):
            if section not in data:
                raise CommandError(f"Demo data must contain '{section}' section.")
        return data
