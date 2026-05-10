from django import template

register = template.Library()


@register.filter
def participants_word(count):
    count = abs(int(count))
    if 11 <= count % 100 <= 14:
        return "участников"
    if count % 10 == 1:
        return "участник"
    if 2 <= count % 10 <= 4:
        return "участника"
    return "участников"
