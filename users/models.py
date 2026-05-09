from io import BytesIO
from uuid import uuid4

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=124)
    surname = models.CharField(max_length=124)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    phone = models.CharField(max_length=12, blank=True, null=True, unique=True)
    github_url = models.URLField(blank=True)
    about = models.TextField(max_length=256, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    class Meta:
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["surname", "name"]),
        ]

    def __str__(self):
        return f"{self.name} {self.surname}".strip() or self.email

    def save(self, *args, **kwargs):
        # Сохраняем единый формат даже при изменениях через админку или скрипты.
        if (
            self.phone
            and self.phone.startswith("8")
            and len(self.phone) == 11
            and self.phone.isdigit()
        ):
            self.phone = "+7" + self.phone[1:]

        if not self.avatar:
            self.avatar.save(
                self._avatar_filename(),
                self._generate_avatar(),
                save=False,
            )
        super().save(*args, **kwargs)

    def _avatar_filename(self):
        return f"default-{uuid4().hex}.png"

    def _generate_avatar(self):
        # Цвет зависит от данных пользователя, поэтому демо-аватары не скачут.
        colors = [
            "#6B8EAD",
            "#7A9E7E",
            "#B08968",
            "#8D6A9F",
            "#5F8D8B",
            "#A87C7C",
        ]
        seed = sum(ord(char) for char in (self.email or self.name or "u"))
        background = colors[seed % len(colors)]
        letter = (self.name[:1] or self.email[:1] or "U").upper()

        image = Image.new("RGB", (256, 256), background)
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 120)
        except OSError:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), letter, font=font)
        x = (256 - (bbox[2] - bbox[0])) / 2
        y = (256 - (bbox[3] - bbox[1])) / 2 - 10
        draw.text((x, y), letter, fill="#FFFFFF", font=font)

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return ContentFile(buffer.getvalue())
