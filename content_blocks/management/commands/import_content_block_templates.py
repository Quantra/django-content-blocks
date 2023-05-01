from django.core.management import call_command
from django.core.management.commands.loaddata import Command as LoaddataCommand
from django.db import transaction

from content_blocks.models import (
    ContentBlock,
    ContentBlockField,
    ContentBlockTemplate,
    ContentBlockTemplateField,
)


class Command(LoaddataCommand):
    """
    Extension of loaddata command. Any ContentBlockTemplate specified in the import json is created or updated to
    match the import data.  For updated objects this includes deleting any related ContentBlockTemplateField which no
    longer exists and creating ContentBlockField objects for existing ContentBlock objects as required.
    """

    help = "Import content block templates from json file."

    # Track the ContentBlockTemplate and ContentBlockTemplateField objects that are imported.
    imported_pks = {
        ContentBlockTemplate: [],
        ContentBlockTemplateField: [],
    }

    def handle(self, *fixture_labels, **options):
        with transaction.atomic():
            super().handle(*fixture_labels, **options)

            verbosity = int(options["verbosity"])

            # Sync ContentBlockTemplateField objects with ContentBlockField objects.
            self.delete_old_content_block_template_fields()

            # Reorder ContentBlockTemplate
            call_command("reorder", "content_blocks.ContentBlockTemplate")

            # Update content blocks cache
            call_command("update_content_blocks_cache")

            if verbosity > 0:
                self.stdout.write(
                    "Content block templates imported!"
                )  # pragma: no cover

    def save_obj(self, obj):
        created = obj.object.pk is None
        saved = super().save_obj(obj)

        if created:
            # Create ContentBlockField objects
            self.add_new_content_block_template_field(obj.object)

        # Track imported object primary keys
        self.imported_pks[obj.object.__class__].append(obj.object.pk)

        return saved

    def add_new_content_block_template_field(self, content_block_template_field):
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

    def delete_old_content_block_template_fields(self):
        """
        For each ContentBlockTemplate specified in the json import delete any related ContentBlockTemplateField
        that is not specified in the json.
        """
        ContentBlockTemplateField.objects.filter(
            content_block_template_id__in=self.imported_pks[ContentBlockTemplate],
        ).exclude(
            id__in=self.imported_pks[ContentBlockTemplateField],
        ).delete()
