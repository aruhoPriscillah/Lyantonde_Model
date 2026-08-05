from decimal import Decimal, InvalidOperation


def format_ugx(value):
    """Format a monetary value as whole Uganda shillings."""
    if value is None or value == "":
        return "UGX 0"

    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return str(value)

    return f"UGX {amount:,.0f}"
