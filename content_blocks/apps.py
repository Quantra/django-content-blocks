import logging

from django.apps import AppConfig, apps
from django.db import OperationalError, ProgrammingError

from content_blocks.conf import settings

logger = logging.getLogger(__name__)


class ContentBlocksConfig(AppConfig):
    name = "content_blocks"
    verbose_name = "Content blocks"

    def ready(self):
        from content_blocks.signals import (  # noqa
            cleanup_media_delete,
            cleanup_media_save,
        )

        if apps.is_installed("dbtemplates"):
            from content_blocks.signals import update_cache_template  # noqa

        if not settings.CONTENT_BLOCKS_DISABLE_CACHE_ON_START:
            try:
                from content_blocks.services.content_block import CacheServices

                CacheServices.get_or_set_cache_all()

            except (OperationalError, ProgrammingError):  # pragma: no cover
                # Migrate hasn't been run yet.
                pass  # pragma: no cover
