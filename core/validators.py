import re
from urllib.parse import urlparse

from django import forms

from core.constants import GITHUB_HOSTS, PHONE_DIGITS_AFTER_PREFIX


PHONE_RE = re.compile(rf"^(8|\+7)\d{{{PHONE_DIGITS_AFTER_PREFIX}}}$")


def validate_github_url(value):
    if not value:
        return value

    host = urlparse(value).netloc.lower()
    if host not in GITHUB_HOSTS:
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
