from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_username(value):
    if value.lower() == 'me':
        raise ValidationError(
            '%(value)s is not a valid username',
            params={'value': value},
        )


def validate_year(value):
    current_year = timezone.now().year
    if value > current_year:
        raise ValidationError(
            f'Year can not be more than {current_year}.',
            params={'value': value},
        )
