from .base import *  # noqa

INSTALLED_APPS = INSTALLED_APPS.copy()  # noqa
INSTALLED_APPS.remove("django_cleanup")
