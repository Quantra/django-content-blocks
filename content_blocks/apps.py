import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class ContentBlocksConfig(AppConfig):
    name = "content_blocks"
    verbose_name = "Content blocks"

    def ready(self):
        from content_blocks.signals import (  # noqa
            cleanup_media_delete,
            cleanup_media_save,
        )
