"""
Content blocks app signals.py
"""
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import Signal, receiver

from content_blocks.models import (
    ContentBlockField,
    ContentBlockFields,
    FileField,
    ImageField,
    VideoField,
)

# A signal we can send after an import finishes.
post_import = Signal()


def cleanup_media(sender, instance, delete=False, **kwargs):
    """
    Delete old media files when no longer needed.
    """
    if kwargs.get("raw", False):
        # Prevent this signal from running during loaddata.
        return

    if instance.id is None:
        return  # New object being created

    object_types = {
        ContentBlockFields.IMAGE_FIELD: "image",
        ContentBlockFields.FILE_FIELD: "file",
        ContentBlockFields.VIDEO_FIELD: "video",
    }

    object_type = object_types.get(instance.field_type)
    if object_type is None:
        return  # pragma: no cover

    if delete:
        old_file = getattr(instance, object_type)
        new_file = None
    else:
        try:
            old_file = getattr(
                ContentBlockField.objects.get(id=instance.id), object_type
            )
            new_file = getattr(instance, object_type)
        except ContentBlockField.DoesNotExist:  # pragma: no cover
            return

    if (
        old_file != new_file
        and not ContentBlockField.objects.filter(**{object_type: old_file})
        .exclude(id=instance.id)
        .exists()
    ):
        old_file.delete(save=False)


@receiver(pre_save, sender=ImageField, dispatch_uid="cleanup_image_media_save")
@receiver(pre_save, sender=FileField, dispatch_uid="cleanup_file_media_save")
@receiver(pre_save, sender=VideoField, dispatch_uid="cleanup_video_media_save")
@receiver(pre_save, sender=ContentBlockField, dispatch_uid="cleanup_media_save")
def cleanup_media_save(sender, instance, **kwargs):
    return cleanup_media(sender, instance, delete=False, **kwargs)


@receiver(pre_delete, sender=ImageField, dispatch_uid="cleanup_image_media_delete")
@receiver(pre_delete, sender=FileField, dispatch_uid="cleanup_file_media_delete")
@receiver(pre_delete, sender=VideoField, dispatch_uid="cleanup_video_media_delete")
@receiver(pre_delete, sender=ContentBlockField, dispatch_uid="cleanup_media_delete")
def cleanup_media_delete(sender, instance, **kwargs):
    return cleanup_media(sender, instance, delete=True, **kwargs)
