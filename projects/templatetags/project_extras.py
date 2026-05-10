from django import template

from core.constants import (
    RUSSIAN_PLURAL_BASE,
    RUSSIAN_PLURAL_FEW_END,
    RUSSIAN_PLURAL_FEW_START,
    RUSSIAN_PLURAL_HUNDRED_BASE,
    RUSSIAN_PLURAL_ONE_ENDING,
    RUSSIAN_PLURAL_TEENS_END,
    RUSSIAN_PLURAL_TEENS_START,
)

register = template.Library()


@register.filter
def participants_word(count):
    count = abs(int(count))
    if (
        RUSSIAN_PLURAL_TEENS_START
        <= count % RUSSIAN_PLURAL_HUNDRED_BASE
        <= RUSSIAN_PLURAL_TEENS_END
    ):
        return "участников"
    if count % RUSSIAN_PLURAL_BASE == RUSSIAN_PLURAL_ONE_ENDING:
        return "участник"
    if (
        RUSSIAN_PLURAL_FEW_START
        <= count % RUSSIAN_PLURAL_BASE
        <= RUSSIAN_PLURAL_FEW_END
    ):
        return "участника"
    return "участников"
