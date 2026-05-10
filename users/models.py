from io import BytesIO
from uuid import uuid4

from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
)
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from core.constants import (
    AVATAR_BACKGROUND_COLORS,
    AVATAR_FONT_NAME,
    AVATAR_FONT_SIZE,
    AVATAR_IMAGE_SIZE,
    AVATAR_TEXT_ANCHOR,
    AVATAR_TEXT_COLOR,
    AVATAR_TEXT_Y_OFFSET,
    PHONE_LOCAL_LENGTH,
    PHONE_MAX_LENGTH,
    USER_ABOUT_MAX_LENGTH,
    USER_NAME_MAX_LENGTH,
    USER_SURNAME_MAX_LENGTH,
)
from users.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=USER_NAME_MAX_LENGTH)
    surname = models.CharField(max_length=USER_SURNAME_MAX_LENGTH)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    phone = models.CharField(
        max_length=PHONE_MAX_LENGTH,
        blank=True,
        null=True,
        unique=True,
    )
    github_url = models.URLField(blank=True)
    about = models.TextField(max_length=USER_ABOUT_MAX_LENGTH, blank=True)
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
            and len(self.phone) == PHONE_LOCAL_LENGTH
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
        seed = sum(ord(char) for char in (self.email or self.name or "u"))
        background = AVATAR_BACKGROUND_COLORS[seed % len(AVATAR_BACKGROUND_COLORS)]
        letter = (self.name[:1] or self.email[:1] or "U").upper()

        image = Image.new("RGB", (AVATAR_IMAGE_SIZE, AVATAR_IMAGE_SIZE), background)
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype(AVATAR_FONT_NAME, AVATAR_FONT_SIZE)
        except OSError:
            font = ImageFont.load_default()

        bbox = draw.textbbox(AVATAR_TEXT_ANCHOR, letter, font=font)
        x = (AVATAR_IMAGE_SIZE - (bbox[2] - bbox[0])) / 2
        y = (
            (AVATAR_IMAGE_SIZE - (bbox[3] - bbox[1])) / 2
            - AVATAR_TEXT_Y_OFFSET
        )
        draw.text((x, y), letter, fill=AVATAR_TEXT_COLOR, font=font)

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return ContentFile(buffer.getvalue())
