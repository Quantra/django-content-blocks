"""
Functions to import and export (from/to JSON)
"""
import itertools
from pathlib import Path

from django.core import serializers
from django.core.management import call_command
from django.db import transaction

from content_blocks.conf import settings
from content_blocks.models import (
    ContentBlock,
    ContentBlockField,
    ContentBlockTemplate,
    ContentBlockTemplateField,
)


class ImportExportServices:
    """
    Service for import and export.
    """

    # todo tests

    # Export ContentBlockTemplate
    @staticmethod
    def export_content_block_templates(queryset=None, file_like=None):
        """
        Export ContentBlockTemplate and related ContentBlockTemplateField to json.
        :param queryset: Queryset of ContentBlockTemplate defaults to ContentBlockTemplate.objects.all()
        :param file_like: Any file like object including HttpResponse and StringIO. This is where the serializer will
        write to.
        :return: Serializer value.
        """
        content_block_templates = queryset or ContentBlockTemplate.objects.all()
        content_block_template_fields = ContentBlockTemplateField.objects.filter(
            content_block_template__in=content_block_templates
        )

        return serializers.serialize(
            "json",
            itertools.chain(content_block_templates, content_block_template_fields),
            stream=file_like,
            use_natural_foreign_keys=True,
            use_natural_primary_keys=True,
        )

    # Import ContentBlockTemplate
    @staticmethod
    def add_new_content_block_template_field(content_block_template_field):
        """
        Add ContentBlockField object for the new ContentBlockTemplateField.
        """
        content_blocks = ContentBlock.objects.filter(
            content_block_template=content_block_template_field.content_block_template
        )

        # Create a new field for existing content blocks
        for content_block in content_blocks:
            ContentBlockField.objects.create(
                template_field=content_block_template_field,
                content_block=content_block,
                field_type=content_block_template_field.field_type,
            )

    @staticmethod
    def delete_old_content_block_template_fields(imported_pks):
        """
        For each ContentBlockTemplate specified in the json import delete any related ContentBlockTemplateField
        that is not specified in the json.
        """
        ContentBlockTemplateField.objects.filter(
            content_block_template_id__in=imported_pks[ContentBlockTemplate],
        ).exclude(
            id__in=imported_pks[ContentBlockTemplateField],
        ).delete()

    @staticmethod
    def import_content_block_templates(stream_or_string, verbosity=0):
        """
        Takes a stream or string and imports it.  Syncs ContentBlockField for ContentBlockTemplate imported by
        deleting ContentBlockField which aren't in the imported data but are in the database. And by creating
        ContentBlockField for ContentBlockTemplateField which are in the imported data but aren't in the database.
        :param verbosity: verbosity option passed to called commands defaults to 0.
        :param stream_or_string:
        """
        imported_pks = {ContentBlockTemplate: [], ContentBlockTemplateField: []}

        with transaction.atomic():
            for obj in serializers.deserialize("json", stream_or_string):
                if obj.object.__class__ not in imported_pks.keys():
                    # Ignore any objects that aren't ContentBlockTemplate or ContentBlockTemplateField
                    continue

                created = obj.object.pk is None
                if not created:
                    # Double check because tests show the above is not always enough
                    model = type(obj.object)
                    created = not model.objects.filter(pk=obj.object.pk).exists()

                obj.save()

                if created and isinstance(obj.object, ContentBlockTemplateField):
                    ImportExportServices.add_new_content_block_template_field(
                        obj.object
                    )

                imported_pks[obj.object.__class__].append(obj.object.pk)

            ImportExportServices.delete_old_content_block_template_fields(imported_pks)

            # Reorder ContentBlockTemplate
            call_command(
                "reorder", "content_blocks.ContentBlockTemplate", verbosity=verbosity
            )

            # Update content blocks cache
            if not settings.CONTENT_BLOCKS_DISABLE_CACHE:
                # todo call service here not management command
                call_command("set_content_blocks_cache", verbosity=verbosity)

    @staticmethod
    def import_content_block_templates_from_file(filepath, verbosity=0):
        """
        Takes a filepath and opens the file and imports it.
        :param filepath: String. The path is relative to
        :return:
        """
        filepath = Path(filepath)

        with filepath.open() as file:
            ImportExportServices.import_content_block_templates(file, verbosity)
