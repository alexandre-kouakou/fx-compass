"""Shared query-parameter validation for the API views."""

from rest_framework.exceptions import ValidationError

from rates.constants import CODES
from .series import RANGES


def currency(request, name, default):
    code = request.query_params.get(name, default).upper()
    if code not in CODES:
        raise ValidationError({name: f"must be one of {', '.join(CODES)}"})
    return code


def pair(request, default_base="USD", default_quote="INR"):
    base = currency(request, "base", default_base)
    quote = currency(request, "quote", default_quote)
    if base == quote:
        raise ValidationError({"quote": "must differ from base"})
    return base, quote


def range_key(request, default="1M"):
    key = request.query_params.get("range", default).upper()
    if key not in RANGES:
        raise ValidationError({"range": f"must be one of {', '.join(RANGES)}"})
    return key


def amount(request, default="1000"):
    try:
        value = float(request.query_params.get("amount", default))
    except ValueError:
        raise ValidationError({"amount": "must be a number"})
    if not 0 < value < 1e12:
        raise ValidationError({"amount": "must be positive"})
    return value
