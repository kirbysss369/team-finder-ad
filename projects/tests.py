from django.test import TestCase
from django.urls import reverse

from users.models import User

from .models import Project, Skill
from .templatetags.project_extras import participants_word


class ProjectSkillApiTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="password",
            name="Мария",
            surname="Иванова",
        )
        self.member = User.objects.create_user(
            email="member@example.com",
            password="password",
            name="Алексей",
            surname="Петров",
        )
        self.project = Project.objects.create(
            owner=self.owner,
            name="TeamFinder",
            description="Pet-project platform",
        )

    def test_owner_can_create_and_attach_skill(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("projects:add_skill", kwargs={"pk": self.project.pk}),
            data={"name": "Django"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["name"], "Django")
        self.assertTrue(payload["created"])
        self.assertTrue(payload["added"])
        self.assertTrue(self.project.skills.filter(name="Django").exists())

    def test_non_owner_cannot_attach_skill(self):
        skill = Skill.objects.create(name="Django")
        self.client.force_login(self.member)

        response = self.client.post(
            reverse("projects:add_skill", kwargs={"pk": self.project.pk}),
            data={"skill_id": skill.pk},
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.project.skills.exists())

    def test_skill_autocomplete_returns_first_ten_matches(self):
        Skill.objects.bulk_create(
            [Skill(name=f"Django {index}") for index in range(12)]
        )

        response = self.client.get(reverse("projects:skills"), {"q": "Django"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 10)


class ProjectViewsTests(TestCase):
    def test_create_project_adds_owner_as_participant(self):
        user = User.objects.create_user(
            email="owner@example.com",
            password="password",
            name="Мария",
            surname="Иванова",
        )
        self.client.force_login(user)

        response = self.client.post(
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
        self.assertEqual(project.owner, user)
        self.assertTrue(project.participants.filter(pk=user.pk).exists())


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
