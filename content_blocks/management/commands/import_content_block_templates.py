import argparse

from django.core.management import call_command
from django.core.management.commands.loaddata import Command as LoaddataCommand
from django.db import transaction
from django.utils.functional import cached_property

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

    infile = None

    def add_arguments(self, parser):
        """
        Add the infile argument, so we can pass file_like objects in call_command.
        """
        super().add_arguments(parser)

        parser.add_argument("--infile", type=argparse.FileType("r"))

    def handle(self, *fixture_labels, **options):
        self.infile = options.get("infile")

        with transaction.atomic():
            super().handle(*fixture_labels, **options)

            verbosity = int(options["verbosity"])

            # Sync ContentBlockTemplateField objects with ContentBlockField objects.
            self.delete_old_content_block_template_fields()

            # Reorder ContentBlockTemplate
            call_command(
                "reorder", "content_blocks.ContentBlockTemplate", verbosity=verbosity
            )

            # Update content blocks cache
            call_command("update_content_blocks_cache", verbosity=verbosity)

            if verbosity > 0:
                self.stdout.write("Content block templates imported!")

    def save_obj(self, obj):
        created = obj.object.pk is None
        saved = super().save_obj(obj)

        if created:
            # Create ContentBlockField objects
            self.add_new_content_block_template_field(obj.object)

        # Track imported object primary keys
        self.imported_pks[obj.object.__class__].append(obj.object.pk)

        return saved

    @cached_property
    def compression_formats(self):
        """
        If an infile is supplied use this in place of stdin so file_like objects can be supplied in call_command.
        """
        compression_formats = super().compression_formats

        if self.infile is not None:
            compression_formats["stdin"] = (lambda *args: self.infile, None)

        return compression_formats

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
