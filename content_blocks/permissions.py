"""
Content Blocks permissions.py
"""
from functools import wraps

from django.core.exceptions import PermissionDenied


def require_ajax(view):
    @wraps(view)
    def _wrapped_view(request, *args, **kwargs):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return view(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return _wrapped_view
