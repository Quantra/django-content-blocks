"""
Content Blocks conf.py
"""
from django.conf import settings as django_settings


class ContentBlocksSettings:
    # Choose the storage backend to use for media files
    # Image, field and video storage settings are use instead of content blocks storage if set.
    CONTENT_BLOCKS_IMAGE_STORAGE = None
    CONTENT_BLOCKS_VIDEO_STORAGE = None
    CONTENT_BLOCKS_FILE_STORAGE = None
    # Use default storage if not set.
    # Support provided here for Django 3.2
    CONTENT_BLOCKS_STORAGE = getattr(django_settings, "STORAGES", {}).get(
        "default", {}
    ).get("BACKEND") or getattr(
        django_settings,
        "DEFAULT_FILE_STORAGE",
        "django.core.files.storage.FileSystemStorage",
    )

    # Set the default status message.  Can be a callable.
    CONTENT_BLOCKS_DEFAULT_STATUS_MESSAGE = ""

    # Mark context for TextField and ContentField as safe. Useful for allowing html in these fields.
    CONTENT_BLOCKS_MARK_SAFE = False

    # Use a textarea widget for TextFields.
    CONTENT_BLOCKS_TEXTFIELD_TEXTAREA = False

    # Pre render content blocks on publish.
    # Useful for populating the cache and/or pre generating django-lazy-srcset images.
    CONTENT_BLOCKS_PRE_RENDER = True
    # Set the cache_timeout when pre rendering
    CONTENT_BLOCKS_PRE_RENDER_CACHE_TIMEOUT = None

    def __getattribute__(self, name):
        try:
            return getattr(django_settings, name)
        except AttributeError:
            return super().__getattribute__(name)


settings = ContentBlocksSettings()
