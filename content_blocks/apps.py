import logging

from django.apps import AppConfig
from django.db import OperationalError, ProgrammingError
from django.template import TemplateDoesNotExist

from content_blocks.conf import settings

logger = logging.getLogger(__name__)


class ContentBlocksConfig(AppConfig):
    name = "content_blocks"
    verbose_name = "Content blocks"

    def ready(self):
        from content_blocks.models import ContentBlock
        from content_blocks.signals import (  # noqa
            cleanup_media_delete,
            cleanup_media_save,
        )

        if not settings.CONTENT_BLOCKS_DISABLE_UPDATE_CACHE_MODEL_CHOICE:
            from content_blocks.signals import update_cache_model_choice  # noqa

        if "dbtemplates" in settings.INSTALLED_APPS:
            from content_blocks.signals import update_cache_template  # noqa

        if not settings.CONTENT_BLOCKS_DISABLE_CACHE_ON_START:
            try:
                for content_block in ContentBlock.objects.filter(
                    parent__isnull=True,
                    content_block_template__template_filename__isnull=False,
                    draft=False,
                ):
                    try:
                        content_block.render()
                    except TemplateDoesNotExist:  # pragma: no cover
                        logger.error(
                            f"No template found when rendering {content_block}"
                        )

            except (OperationalError, ProgrammingError):  # pragma: no cover
                # Migrate hasn't been run yet.
                pass  # pragma: no cover
