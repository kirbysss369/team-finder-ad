import re
from urllib.parse import urlparse

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordChangeForm

from .models import User


PHONE_RE = re.compile(r"^(8|\+7)\d{10}$")


def validate_github_url(value):
    if not value:
        return value

    host = urlparse(value).netloc.lower()
    if host not in {"github.com", "www.github.com"}:
        raise forms.ValidationError("Ссылка должна вести на GitHub.")
    return value


def normalize_phone(value):
    value = (value or "").strip()
    if not value:
        return None

    if not PHONE_RE.match(value):
        raise forms.ValidationError(
            "Телефон должен быть в формате 8XXXXXXXXXX или +7XXXXXXXXXX."
        )

    if value.startswith("8"):
        return "+7" + value[1:]
    return value


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["name", "surname", "email", "password"]
        labels = {
            "name": "Имя",
            "surname": "Фамилия",
            "email": "Email",
        }

    def clean_email(self):
        return self.cleaned_data["email"].lower()

    def save(self, commit=True):
        data = self.cleaned_data
        user = User(
            name=data["name"],
            surname=data["surname"],
            email=data["email"],
        )
        user.set_password(data["password"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.user = None

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            self.user = authenticate(
                self.request,
                username=email.lower(),
                password=password,
            )
            if self.user is None:
                raise forms.ValidationError("Неверный имейл или пароль")
        return cleaned_data

    def get_user(self):
        return self.user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["name", "surname", "avatar", "about", "phone", "github_url"]
        labels = {
            "name": "Имя",
            "surname": "Фамилия",
            "avatar": "Аватар",
            "about": "О себе",
            "phone": "Телефон",
            "github_url": "GitHub",
        }
        widgets = {
            "avatar": forms.FileInput(attrs={"accept": "image/*"}),
            "about": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data.get("phone"))
        if not phone:
            return None

        # Проверяем оба варианта записи номера до сохранения в едином формате.
        phone_variants = {phone, "8" + phone[2:]}
        duplicate = User.objects.filter(phone__in=phone_variants)
        if self.instance.pk:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise forms.ValidationError("Такой номер телефона уже используется.")
        return phone

    def clean_github_url(self):
        return validate_github_url(self.cleaned_data.get("github_url"))


class UserPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(label="Текущий пароль", widget=forms.PasswordInput)
    new_password1 = forms.CharField(label="Новый пароль", widget=forms.PasswordInput)
    new_password2 = forms.CharField(
        label="Подтвердите новый пароль",
        widget=forms.PasswordInput,
    )
