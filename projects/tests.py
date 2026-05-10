from http import HTTPStatus
from io import StringIO

from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from core.constants import SKILL_AUTOCOMPLETE_LIMIT
from projects.models import Project, Skill
from projects.templatetags.project_extras import participants_word
from users.models import User


class ProjectSkillApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            email="owner@example.com",
            password="password",
            name="Мария",
            surname="Иванова",
        )
        cls.member = User.objects.create_user(
            email="member@example.com",
            password="password",
            name="Алексей",
            surname="Петров",
        )
        cls.project = Project.objects.create(
            owner=cls.owner,
            name="TeamFinder",
            description="Pet-project platform",
        )
        cls.owner_client = Client()
        cls.owner_client.force_login(cls.owner)
        cls.member_client = Client()
        cls.member_client.force_login(cls.member)

    def test_owner_can_create_and_attach_skill(self):
        response = self.owner_client.post(
            reverse("projects:add_skill", kwargs={"pk": self.project.pk}),
            data={"name": "Django"},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        payload = response.json()
        self.assertEqual(payload["name"], "Django")
        self.assertTrue(payload["created"])
        self.assertTrue(payload["added"])
        self.assertTrue(self.project.skills.filter(name="Django").exists())

    def test_non_owner_cannot_attach_skill(self):
        skill = Skill.objects.create(name="Django")

        response = self.member_client.post(
            reverse("projects:add_skill", kwargs={"pk": self.project.pk}),
            data={"skill_id": skill.pk},
        )

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertFalse(self.project.skills.exists())

    def test_skill_autocomplete_returns_first_ten_matches(self):
        Skill.objects.bulk_create(
            [
                Skill(name=f"Django {index}")
                for index in range(SKILL_AUTOCOMPLETE_LIMIT + 1)
            ]
        )

        response = self.client.get(reverse("projects:skills"), {"q": "Django"})

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.json()), SKILL_AUTOCOMPLETE_LIMIT)


class ProjectViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="owner@example.com",
            password="password",
            name="Мария",
            surname="Иванова",
        )
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)

    def test_create_project_adds_owner_as_participant(self):
        response = self.user_client.post(
            reverse("projects:create"),
            {
                "name": "Новый проект",
                "description": "Описание",
                "github_url": "https://github.com/owner/project",
                "status": Project.STATUS_OPEN,
            },
        )

        project = Project.objects.get(name="Новый проект")
        self.assertRedirects(
            response,
            reverse("projects:detail", kwargs={"pk": project.pk}),
        )
        self.assertEqual(project.owner, self.user)
        self.assertTrue(project.participants.filter(pk=self.user.pk).exists())


class ProjectTemplateFilterTests(TestCase):
    def test_participants_word_uses_russian_plural_form(self):
        cases = {
            1: "участник",
            2: "участника",
            5: "участников",
            11: "участников",
            21: "участник",
        }

        for count, expected in cases.items():
            with self.subTest(count=count):
                self.assertEqual(participants_word(count), expected)


class SeedDemoCommandTests(TestCase):
    def test_seed_demo_loads_default_json_data(self):
        output = StringIO()

        call_command("seed_demo", stdout=output)

        self.assertIn("Demo data is ready", output.getvalue())
        self.assertTrue(User.objects.filter(email="maria@yandex.ru").exists())
        self.assertTrue(Project.objects.filter(skills__name="Django").exists())
