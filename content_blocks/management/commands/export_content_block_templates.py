from django.core.management import BaseCommand
from import_export import ImportExportServices


class Command(BaseCommand):
    help = "Export content block templates to json."

    def handle(self, *args, **options):
        """
        Export ContentBlockTemplate and associated ContentBlockTemplateField to json via stdout.
        The output can be used for import_content_block_templates management command.
        """
        ImportExportServices.export_content_block_templates(file_like=self.stdout)
