from django.test import TestCase
from django.urls import reverse

from .forms import ProfileForm
from .models import User


class UserAuthTests(TestCase):
    def test_register_creates_and_logs_in_user(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "name": "Мария",
                "surname": "Иванова",
                "email": "maria@example.com",
                "password": "password",
            },
        )

        self.assertRedirects(response, reverse("projects:list"))
        self.assertTrue(User.objects.filter(email="maria@example.com").exists())
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_by_email(self):
        User.objects.create_user(
            email="alex@example.com",
            password="password",
            name="Алексей",
            surname="Петров",
        )

        response = self.client.post(
            reverse("users:login"),
            {"email": "alex@example.com", "password": "password"},
        )

        self.assertRedirects(response, reverse("projects:list"))
        self.assertIn("_auth_user_id", self.client.session)


class ProfileFormTests(TestCase):
    def test_phone_is_normalized_and_unique(self):
        existing = User.objects.create_user(
            email="existing@example.com",
            password="password",
            name="Ольга",
            surname="Смирнова",
            phone="+79000000001",
        )
        user = User.objects.create_user(
            email="new@example.com",
            password="password",
            name="Новый",
            surname="Пользователь",
        )

        form = ProfileForm(
            data={
                "name": user.name,
                "surname": user.surname,
                "about": "",
                "phone": "89000000001",
                "github_url": "https://github.com/new-user",
            },
            instance=user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)
        self.assertEqual(existing.phone, "+79000000001")

    def test_github_url_must_point_to_github(self):
        user = User.objects.create_user(
            email="new@example.com",
            password="password",
            name="Новый",
            surname="Пользователь",
        )
        form = ProfileForm(
            data={
                "name": user.name,
                "surname": user.surname,
                "about": "",
                "phone": "+79000000009",
                "github_url": "https://example.com/user",
            },
            instance=user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("github_url", form.errors)
