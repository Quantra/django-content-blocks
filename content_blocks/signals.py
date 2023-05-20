"""
Content blocks app signals.py
"""
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, OperationalError, ProgrammingError
from django.db.migrations.recorder import MigrationRecorder
from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver

from content_blocks.conf import settings
from content_blocks.models import (
    ContentBlock,
    ContentBlockField,
    ContentBlockFields,
    FileField,
    ImageField,
    VideoField,
)
from content_blocks.services.content_block import CacheServices

if not settings.CONTENT_BLOCKS_DISABLE_UPDATE_CACHE_MODEL_CHOICE:

    @receiver(post_save, dispatch_uid="update_cache_model_choice_save")
    @receiver(post_delete, dispatch_uid="update_cache_model_choice_delete")
    def update_cache_model_choice(sender, instance, **kwargs):
        """
        Clear the cache for content blocks when related objects are saved. Model choice fields.
        """
        # todo:
        #  remove this.  updating cache is flakey at best because changes to related objects can also require a
        #  cache update but this won't trigger it.  It is better to document the need to set no_cache=True for
        #  ContentBlockTemplate containing ContentBlockModelChoiceField or to manage updating the cache yourself.
        if kwargs.get("raw", False):
            # Prevent this signal from running during loaddata.
            return

        if sender == MigrationRecorder.Migration:
            # Do not run the signal for MigrationRecorder.Migration otherwise migrations will fail
            return

        try:
            content_block_fields = ContentBlockField.objects.filter(
                model_choice_content_type=ContentType.objects.get_for_model(sender),
                model_choice_object_id=getattr(instance, "id", None),
            )

            content_blocks = ContentBlock.objects.filter(
                content_block_fields__in=content_block_fields
            )

            CacheServices.set_cache_all(queryset=content_blocks)

        except (
            OperationalError,
            ProgrammingError,
            IntegrityError,
            ContentType.DoesNotExist,
        ):  # pragma: no cover
            """
            Content blocks not migrated yet.
            """
            return


if "dbtemplates" in settings.INSTALLED_APPS:
    from dbtemplates.models import Template

    @receiver(post_save, sender=Template, dispatch_uid="update_cache_template_save")
    @receiver(post_delete, sender=Template, dispatch_uid="update_cache_template_delete")
    def update_cache_template(sender, instance, **kwargs):
        """
        Update the cache for content blocks when their db template is saved.
        """
        if kwargs.get("raw", False):
            # Prevent this signal from running during loaddata.
            return

        content_blocks = ContentBlock.objects.filter(
            content_block_template__template_filename=instance.name.split("/")[-1]
        )

        CacheServices.set_cache_all(queryset=content_blocks)


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
def cleanup_media_save(sender, instance, **kwargs):
    return cleanup_media(sender, instance, delete=False, **kwargs)


@receiver(pre_delete, sender=ImageField, dispatch_uid="cleanup_image_media_delete")
@receiver(pre_delete, sender=FileField, dispatch_uid="cleanup_file_media_delete")
@receiver(pre_delete, sender=VideoField, dispatch_uid="cleanup_video_media_delete")
def cleanup_media_delete(sender, instance, **kwargs):
    return cleanup_media(sender, instance, delete=True, **kwargs)
