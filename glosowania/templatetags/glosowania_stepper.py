from django import template

from glosowania.stepper import get_stepper_counts

register = template.Library()


@register.simple_tag
def glosowania_counts():
    return get_stepper_counts()
