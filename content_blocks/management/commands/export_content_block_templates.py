from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    help = "Export content block templates to json."

    def handle(self, *args, **options):
        """
        A convenience to run instead of:
        $ python3 manage.py dumpdata \
        content_blocks.ContentBlockTemplate content_blocks.ContentBlockTemplateField \
        --natural-primary --natural-foreign --format json
        The output can be used for import_content_block_templates management command.
        """
        call_command(
            "dumpdata",
            "content_blocks.ContentBlockTemplate",
            "content_blocks.ContentBlockTemplateField",
            natural_primary=True,
            natural_foreign=True,
            format="json",
            *args,
            **options
        )
