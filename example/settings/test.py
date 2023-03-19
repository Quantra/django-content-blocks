from django.utils import timezone

from .base import *  # noqa

CONTENT_BLOCKS_DEFAULT_STATUS_MESSAGE = (
    lambda: f"&copy; Shy Studios Ltd {timezone.now().strftime('%Y')}"
)
