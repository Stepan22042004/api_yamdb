from django.core.exceptions import ValidationError


def validate_username(value):
    if value.lower() == 'me':
        raise ValidationError(
            '%(value)s is not a valid username',
            params={'value': value},
        )
