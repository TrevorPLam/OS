"""
Helpers for platform-level roles.
"""


def resolve_platform_role(user):
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        return "break_glass"
    if user.is_staff:
        return "operator"
    return None
