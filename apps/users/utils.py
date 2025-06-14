import re
from django.core.exceptions import ValidationError


def validate_phone_number(value):
    pattern = r'^\+998\d{9}$'
    if not re.fullmatch(pattern, value):
        raise ValidationError("Invalid phone number format. Example: +998901234567")
