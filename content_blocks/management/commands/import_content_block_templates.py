from django.core.management import BaseCommand

from content_blocks.models import ContentBlockTemplate, ContentBlockTemplateField
from content_blocks.services.content_block_template import ImportExportServices


class Command(BaseCommand):
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
        parser.add_argument(
            "args",
            metavar="filepath",
            nargs=1,
            help="Path to json file.",
        )

    def handle(self, filepath, **options):
        verbosity = int(options["verbosity"])

        ImportExportServices.import_content_block_templates_from_file(
            filepath, verbosity
        )

        if verbosity > 0:
            self.stdout.write("Content block templates imported!")
